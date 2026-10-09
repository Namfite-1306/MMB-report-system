import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const args = process.argv.slice(2);
const readArg = (name) => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : null;
};
const hasFlag = (name) => args.includes(name);
const resultPath = readArg("--result");
const outputPath = readArg("--output");
const previewDir = readArg("--preview-dir");
const force = hasFlag("--force");

if (!resultPath || !outputPath) {
  throw new Error("Cần --result <json> và --output <xlsx>.");
}
try {
  await fs.access(outputPath);
  if (!force) throw new Error(`File đã tồn tại: ${outputPath}. Dùng --force để cập nhật có chủ đích.`);
} catch (error) {
  if (error?.code !== "ENOENT" && !String(error?.message).includes("Dùng --force")) throw error;
  if (String(error?.message).includes("Dùng --force")) throw error;
}

const result = JSON.parse(await fs.readFile(resultPath, "utf8"));
const indicators = result?.data?.indicators ?? [];
const sources = result?.sources ?? [];
const metadata = result?.data?.metadata ?? {};
const sourceIds = new Set(sources.map((item) => item.source_id));

const assert = (condition, message) => {
  if (!condition) throw new Error(`Kiểm tra workbook thất bại: ${message}`);
};
const toDate = (value) => {
  if (!value) return null;
  const day = String(value).slice(0, 10);
  const parsed = new Date(`${day}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) throw new Error(`Ngày không hợp lệ: ${value}`);
  return parsed;
};
const joinValues = (value) => Array.isArray(value) ? value.join("; ") : (value ?? "");
const stringifyValue = (value) => {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value, null, 0);
  return value;
};
const columnName = (count) => String.fromCharCode(64 + count);

assert(indicators.length > 0, "Không có indicators trong kết quả JSON.");
assert(indicators.every((item) => item.source_id === null || sourceIds.has(item.source_id)), "Có source_id không tồn tại trong Sources.");
const fx = indicators.find((item) => item.group === "exchange_rate");
assert(fx && typeof fx.value === "number" && fx.value === 24337, "Tỷ giá phải là số 24337 VND/USD.");

const workbook = Workbook.create();
const analysisSheet = workbook.worksheets.add("Analysis");
const macroSheet = workbook.worksheets.add("Macro_Data");
const sourceSheet = workbook.worksheets.add("Sources");
const fontFamily = "Arial";
const colors = {
  navy: "#1F4E78",
  blue: "#5B9BD5",
  lightBlue: "#D9EAF7",
  lightGray: "#E7E6E6",
  text: "#1F2937",
  border: "#B4C6E7",
};

function styleBase(sheet, usedRange) {
  sheet.showGridLines = false;
  sheet.getRange(usedRange).format.font = { name: fontFamily, size: 10, color: colors.text };
  sheet.getRange(usedRange).format.verticalAlignment = "center";
}

function styleTitle(sheet, title, lastColumn) {
  sheet.getRange("A2").values = [[title]];
  sheet.getRange("A2").format.font = { name: fontFamily, size: 14, bold: true, color: colors.navy };
  sheet.getRange(`A3:${lastColumn}3`).format.borders = {
    bottom: { style: "thin", color: colors.navy },
  };
  sheet.getRange("A2").format.rowHeight = 24;
}

function addTable(sheet, range, name) {
  const table = sheet.tables.add(range, true, name);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  table.showBandedColumns = false;
  return table;
}

function addSection(sheet, startRow, title, headers, rows, tableName) {
  const safeRows = rows.length ? rows : [["Không có", "", ...headers.slice(2).map(() => "")]];
  const lastColumn = columnName(headers.length);
  sheet.getRange(`A${startRow}:${lastColumn}${startRow}`).values = [[title, ...headers.slice(1).map(() => "")]];
  sheet.getRange(`A${startRow}:${lastColumn}${startRow}`).format = {
    fill: colors.lightBlue,
    font: { name: fontFamily, size: 10, bold: true, color: colors.navy },
    borders: { preset: "outside", style: "thin", color: colors.border },
  };
  const headerRow = startRow + 1;
  const dataStart = headerRow + 1;
  const dataEnd = dataStart + safeRows.length - 1;
  sheet.getRange(`A${headerRow}:${lastColumn}${headerRow}`).values = [headers];
  sheet.getRange(`A${dataStart}`).write(safeRows);
  addTable(sheet, `A${headerRow}:${lastColumn}${dataEnd}`, tableName);
  sheet.getRange(`A${dataStart}:${lastColumn}${dataEnd}`).format.wrapText = true;
  sheet.getRange(`A${dataStart}:${lastColumn}${dataEnd}`).format.verticalAlignment = "top";
  return { headerRow, dataStart, dataEnd, nextRow: dataEnd + 2 };
}

// Macro_Data
styleTitle(macroSheet, "Dữ liệu vĩ mô", "L");
macroSheet.getRange("A4").values = [["Snapshot xác minh đến 2025-01-06. Lần chạy này không tải dữ liệu mới."]];
macroSheet.getRange("A4").format.font = { name: fontFamily, size: 10, italic: true, color: "#666666" };
const macroHeaders = [
  "indicator_id", "Tên chỉ tiêu", "Giá trị", "Đơn vị", "Cách đo", "Kỳ dữ liệu",
  "Tần suất", "Ngày công bố", "Ngày hiệu lực", "source_id", "Trạng thái dữ liệu", "Ghi chú",
];
const macroRows = indicators.map((item) => [
  item.indicator_id,
  item.name,
  item.value ?? null,
  item.unit,
  item.measurement ?? "",
  item.data_period ?? "",
  item.frequency ?? "",
  toDate(item.publication_date),
  toDate(item.effective_date ?? item.valid_from),
  item.source_id ?? "",
  item.value === null || item.value === undefined ? "Thiếu dữ liệu" : "Có dữ liệu",
  item.value_note ?? (item.value === null || item.value === undefined ? "Không có quan sát phù hợp ngày chốt." : ""),
]);
macroSheet.getRange("A5:L5").values = [macroHeaders];
macroSheet.getRange("A6").write(macroRows);
addTable(macroSheet, `A5:L${5 + macroRows.length}`, "MacroDataTable");
macroSheet.freezePanes.freezeRows(5);
macroSheet.getRange(`H6:I${5 + macroRows.length}`).format.numberFormat = "yyyy-mm-dd";
indicators.forEach((item, index) => {
  const row = 6 + index;
  if (String(item.unit).startsWith("ratio")) macroSheet.getRange(`C${row}`).format.numberFormat = "0.00%";
  if (item.unit === "VND/USD") macroSheet.getRange(`C${row}`).format.numberFormat = "#,##0";
});
macroSheet.getRange(`B6:B${5 + macroRows.length}`).format.wrapText = true;
macroSheet.getRange(`E6:E${5 + macroRows.length}`).format.wrapText = true;
macroSheet.getRange(`L6:L${5 + macroRows.length}`).format.wrapText = true;
macroSheet.getRange("A:A").format.columnWidth = 42;
macroSheet.getRange("B:B").format.columnWidth = 38;
macroSheet.getRange("C:C").format.columnWidth = 14;
macroSheet.getRange("D:D").format.columnWidth = 16;
macroSheet.getRange("E:E").format.columnWidth = 56;
macroSheet.getRange("F:F").format.columnWidth = 22;
macroSheet.getRange("G:G").format.columnWidth = 14;
macroSheet.getRange("H:I").format.columnWidth = 15;
macroSheet.getRange("J:J").format.columnWidth = 32;
macroSheet.getRange("K:K").format.columnWidth = 18;
macroSheet.getRange("L:L").format.columnWidth = 58;
macroSheet.getRange(`A6:L${5 + macroRows.length}`).format.rowHeight = 42;
styleBase(macroSheet, `A2:L${5 + macroRows.length}`);

// Sources
styleTitle(sourceSheet, "Nguồn dữ liệu", "J");
sourceSheet.getRange("A4").values = [["Ngày công bố và ngày truy cập là hai trường độc lập. Loại nguồn không tự động đồng nghĩa dữ liệu thiếu."]];
sourceSheet.getRange("A4").format.font = { name: fontFamily, size: 10, italic: true, color: "#666666" };
const sourceHeaders = [
  "source_id", "Đơn vị công bố", "Tiêu đề", "URL", "Kỳ dữ liệu", "Ngày công bố",
  "Ngày truy cập", "Loại nguồn", "Quy ước chất lượng", "Ghi chú chất lượng",
];
const sourceRows = sources.map((item) => [
  item.source_id,
  item.publisher,
  item.title,
  item.url,
  item.data_period,
  toDate(item.publication_date),
  toDate(item.access_date),
  item.classification,
  item.quality_treatment ?? "",
  item.quality_note ?? "",
]);
sourceSheet.getRange("A5:J5").values = [sourceHeaders];
sourceSheet.getRange("A6").write(sourceRows);
addTable(sourceSheet, `A5:J${5 + sourceRows.length}`, "SourcesTable");
sourceSheet.freezePanes.freezeRows(5);
sourceSheet.getRange(`F6:G${5 + sourceRows.length}`).format.numberFormat = "yyyy-mm-dd";
sourceSheet.getRange(`B6:E${5 + sourceRows.length}`).format.wrapText = true;
sourceSheet.getRange(`J6:J${5 + sourceRows.length}`).format.wrapText = true;
sourceSheet.getRange("A:A").format.columnWidth = 34;
sourceSheet.getRange("B:B").format.columnWidth = 34;
sourceSheet.getRange("C:C").format.columnWidth = 50;
sourceSheet.getRange("D:D").format.columnWidth = 68;
sourceSheet.getRange("E:E").format.columnWidth = 32;
sourceSheet.getRange("F:G").format.columnWidth = 15;
sourceSheet.getRange("H:H").format.columnWidth = 15;
sourceSheet.getRange("I:I").format.columnWidth = 32;
sourceSheet.getRange("J:J").format.columnWidth = 62;
sourceSheet.getRange(`A6:J${5 + sourceRows.length}`).format.rowHeight = 48;
styleBase(sourceSheet, `A2:J${5 + sourceRows.length}`);

// Analysis
analysisSheet.tabColor = colors.navy;
styleTitle(analysisSheet, `Phân tích vĩ mô - ${result.ticker}`, "G");
const input = metadata.input ?? {};
const dataset = metadata.dataset ?? {};
const statusDetails = metadata.status_details ?? {};
const metadataRows = [
  ["schema_version", result.schema_version, "Giữ nguyên từ input"],
  ["run_id", result.run_id, "Giữ nguyên từ input"],
  ["ticker", result.ticker, "Giữ nguyên từ input"],
  ["exchange", input.exchange ?? "", "Giữ nguyên từ input"],
  ["industry", input.industry ?? "", "Giữ nguyên tên ngành đầu vào"],
  ["as_of_date", toDate(result.as_of_date), "Ngày chốt dữ liệu"],
  ["analysis_period.start_date", toDate(input.analysis_period?.start_date), "Ngày bắt đầu phân tích"],
  ["analysis_period.end_date", toDate(input.analysis_period?.end_date), "Ngày kết thúc phân tích"],
  ["investment_horizon", stringifyValue(input.investment_horizon), `Trọng tâm: ${metadata.investment_horizon_focus ?? ""}`],
  ["status", result.status, "partial trong mẫu do quy ước chất lượng nguồn tỷ giá; giá trị số không bị thiếu"],
  ["status_reason_codes", joinValues(statusDetails.reason_codes), statusDetails.meaning ?? ""],
  ["dataset_id", dataset.dataset_id ?? "", ""],
  ["dataset_version", dataset.dataset_version ?? "", ""],
  ["verified_through", toDate(dataset.verified_through), "Không trình bày snapshot này là dữ liệu hiện tại"],
  ["snapshot_kind", dataset.snapshot_kind ?? "", ""],
  ["snapshot_compiled_at", toDate(dataset.snapshot_compiled_at), "Ngày biên soạn snapshot cục bộ"],
  ["refresh_behavior", dataset.refresh_behavior ?? "", "generate_macro.py tái tạo output từ snapshot; không tải dữ liệu mới"],
  ["network_fetch_performed", dataset.network_fetch_performed ?? false, "false = không có tải mạng trong lần chạy"],
  ["collection_method", dataset.collection_method ?? "", ""],
  ["cache_key", dataset.cache_key ?? "", "Dùng chung dữ liệu vĩ mô cho nhiều mã cùng ngày chốt"],
  ["output_generated_at", metadata.output_generated_at ? toDate(metadata.output_generated_at) : null, "Ngày tạo output; khác ngày công bố/hiệu lực/truy cập"],
  ["industry_mapping_scope", "5 nhóm", "Công nghệ, ngân hàng, bất động sản, sản xuất xuất khẩu, tiêu dùng/bán lẻ"],
];
let section = addSection(analysisSheet, 5, "Input và metadata", ["Trường", "Giá trị", "Ghi chú"], metadataRows, "AnalysisMetadataTable");
const metadataStart = section.dataStart;
metadataRows.forEach((row, index) => {
  if (row[1] instanceof Date) analysisSheet.getRange(`B${metadataStart + index}`).format.numberFormat = "yyyy-mm-dd";
});
let nextRow = section.nextRow;
const summary = result.data.macro_summary ?? {};
const summaryRows = [
  ...(summary.observations ?? []).map((item) => ["Quan sát", item.statement, joinValues(item.indicator_ids), joinValues(item.source_ids)]),
  ...(summary.calculated_results ?? []).map((item) => ["Tính toán", `${item.name}: ${item.value} ${item.unit}; công thức ${item.formula}`, joinValues(item.indicator_ids), joinValues(item.source_ids)]),
  ...(summary.assessment ? [["Nhận định", summary.assessment.statement, joinValues(summary.assessment.indicator_ids), joinValues(summary.assessment.source_ids)]] : []),
];
section = addSection(analysisSheet, nextRow, "Tóm tắt vĩ mô", ["Loại", "Nội dung", "indicator_ids", "source_ids"], summaryRows, "MacroSummaryTable");
nextRow = section.nextRow;
const impactRows = (result.data.industry_impacts ?? []).map((item) => [
  item.direction,
  item.mechanism,
  joinValues(item.conditions),
  joinValues(item.company_checks),
  joinValues(item.evidence?.map((entry) => entry.indicator_id)),
  joinValues(item.evidence?.map((entry) => entry.source_id)),
  item.investment_horizon_focus,
]);
section = addSection(analysisSheet, nextRow, "Tác động ngành", ["Hướng", "Cơ chế", "Điều kiện", "Cần kiểm tra ở doanh nghiệp", "indicator_ids", "source_ids", "Trọng tâm thời hạn"], impactRows, "IndustryImpactsTable");
nextRow = section.nextRow;
const opportunityRiskRows = [
  ...(result.data.opportunities ?? []).map((item) => ["Cơ hội", item.statement, joinValues(item.conditions), joinValues(item.indicator_ids), joinValues(item.source_ids)]),
  ...(result.data.risks ?? []).map((item) => ["Rủi ro", item.statement, joinValues(item.conditions), joinValues(item.indicator_ids), joinValues(item.source_ids)]),
];
section = addSection(analysisSheet, nextRow, "Cơ hội và rủi ro có điều kiện", ["Loại", "Nội dung", "Điều kiện", "indicator_ids", "source_ids"], opportunityRiskRows, "OpportunityRiskTable");
nextRow = section.nextRow;
const reviewRows = [
  ...(result.warnings ?? []).map((item) => ["Warning", item.code, item.message, item.affects_status === true ? "Có" : "Không"]),
  ...(result.errors ?? []).map((item) => ["Error", item.code, item.message, "Có"]),
  ...(result.data.limitations ?? []).map((item) => ["Limitation", "", item, "Không"]),
];
section = addSection(analysisSheet, nextRow, "Warnings, errors và limitations", ["Loại", "Mã", "Nội dung", "Ảnh hưởng status"], reviewRows, "ReviewNotesTable");
const analysisEnd = section.dataEnd;
analysisSheet.freezePanes.freezeRows(6);
analysisSheet.getRange("A:A").format.columnWidth = 28;
analysisSheet.getRange("B:B").format.columnWidth = 68;
analysisSheet.getRange("C:D").format.columnWidth = 38;
analysisSheet.getRange("E:F").format.columnWidth = 32;
analysisSheet.getRange("G:G").format.columnWidth = 20;
analysisSheet.getRange(`A6:G${analysisEnd}`).format.rowHeight = 38;
styleBase(analysisSheet, `A2:G${analysisEnd}`);

workbook.recalculate();

const inspections = {};
for (const [sheetName, range] of [
  ["Macro_Data", `A1:L${5 + macroRows.length}`],
  ["Sources", `A1:J${5 + sourceRows.length}`],
  ["Analysis", `A1:G${analysisEnd}`],
]) {
  const inspected = await workbook.inspect({
    kind: "table",
    range: `${sheetName}!${range}`,
    include: "values,formulas",
    tableMaxRows: sheetName === "Analysis" ? 18 : 12,
    tableMaxCols: 12,
    maxChars: 5000,
  });
  inspections[sheetName] = inspected.ndjson;
}
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
  maxChars: 3000,
});
assert(!formulaErrors.ndjson.includes("#REF!") && !formulaErrors.ndjson.includes("#DIV/0!"), "Có lỗi công thức trong workbook.");

if (previewDir) {
  await fs.mkdir(previewDir, { recursive: true });
  for (const [sheetName, range] of [
    ["Analysis", `A1:G${analysisEnd}`],
    ["Macro_Data", `A1:L${5 + macroRows.length}`],
    ["Sources", `A1:J${5 + sourceRows.length}`],
  ]) {
    const image = await workbook.render({ sheetName, range, scale: 1, format: "png" });
    await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await image.arrayBuffer()));
  }
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

const reloaded = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const reloadedMacro = reloaded.worksheets.getItem("Macro_Data");
const reloadedSources = reloaded.worksheets.getItem("Sources");
const reloadedAnalysis = reloaded.worksheets.getItem("Analysis");
const macroValues = reloadedMacro.getRange(`A5:L${5 + macroRows.length}`).values;
const fxRow = macroValues.find((row) => row[0] === fx.indicator_id);
assert(fxRow && typeof fxRow[2] === "number" && fxRow[2] === 24337, "Tỷ giá sau export/import không còn là số 24337.");
const macroSourceIds = new Set(macroValues.slice(1).map((row) => row[9]).filter(Boolean));
assert([...macroSourceIds].every((id) => sourceIds.has(id)), "source_id giữa Macro_Data và Sources không khớp.");
const sourceValues = reloadedSources.getRange(`A5:J${5 + sourceRows.length}`).values;
assert(sourceValues.slice(1).length === sources.length, "Số nguồn trong Excel không khớp JSON.");
const analysisValues = reloadedAnalysis.getRange(`A1:C${analysisEnd}`).values;
const statusRow = analysisValues.find((row) => row[0] === "status");
assert(statusRow && statusRow[1] === result.status, "Status trong Analysis không khớp JSON.");
const runIdRow = analysisValues.find((row) => row[0] === "run_id");
assert(runIdRow && runIdRow[1] === result.run_id, "run_id trong Analysis không khớp JSON.");

console.log(JSON.stringify({
  output: path.resolve(outputPath),
  status: result.status,
  indicator_count: indicators.length,
  source_count: sources.length,
  fx_value: fxRow[2],
  source_ids_match: true,
  input_status_match: true,
  formula_error_scan: "ok",
  previews: previewDir ? path.resolve(previewDir) : null,
}, null, 2));
