// Configured groups copied from member 2's industry/data_loader.py.
const groups = [
  ['1750','Sản xuất Thép & Kim loại','HPG NKG HSG VGS TVN TLH POM'],
  ['9530','Công nghệ thông tin','FPT CMG ELC ITD SAM SGT'],
  ['8350','Ngân hàng','VCB BID CTG TCB MBB ACB VPB HDB STB VIB TPB LPB SHB'],
  ['5370','Bán lẻ','MWG FRT DGW PNJ PET'],
  ['8630','Bất động sản','VHM VIC VRE KDH NLG DXG PDR DIG'],
  ['8770','Chứng khoán','SSI VCI VND HCM MBS SHS FTS BSI']
];
export function resolveIndustry(ticker) {
  const group=groups.find(g=>g[2].split(' ').includes(ticker));
  return group ? {code:group[0],name:group[1]} : {code:'UNCLASSIFIED',name:'Chưa phân loại'};
}
