// Do not retry writes automatically: a lost response may follow a completed run.
export async function requestJSON(route, body, fetcher=globalThis.fetch) {
  let response;
  try {
    response=await fetcher(route,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  } catch {
    throw new Error(body===undefined
      ? 'Không kết nối được máy chủ. Kiểm tra app đang chạy rồi bấm Thử kết nối lại.'
      : 'Mất kết nối khi gửi yêu cầu. Kết quả có thể đã được lưu; bấm Thử kết nối lại và mở lần phân tích trước khi chạy lại.');
  }
  let result;
  try {result=await response.json();}
  catch {throw new Error('Máy chủ trả về phản hồi không hợp lệ (HTTP '+response.status+'). Kiểm tra app đang chạy đúng cổng.');}
  if(!response.ok){const error=new Error(result.error || 'Yêu cầu thất bại (HTTP '+response.status+').');error.status=response.status;throw error;}
  return result;
}
