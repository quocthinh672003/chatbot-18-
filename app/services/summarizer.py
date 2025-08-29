# summarization helpers (reserved for future expansion)

build chatbot 18 với api venice
- system phải đáp ứng được nhiều user
- system AI agent phải hiểu được ngữ cảnh trước đó của cuộc hội thoại
- khi mà kill app thì bị reset state thì chúng ta phải xử lý như nào
có chức năng chat với người dùng (chat kiểu gì cũng được). Nghiên cứu phần tóm tắt cuộc trò chuyện và truyền lịch sử của cuộc trò chuyện vào mỗi tin nhắn (ưu tiên dùng redis) 
https://langchain-ai.github.io/langgraph/how-tos/memory/add-memory/#add-short-term-memory

- tham khảo
(
1. Phân Tích Tổng Quan
 
 
Mục tiêu
 
Xây dựng một AI Agent tự hành (autonomous agent) sử dụng LangChain. Agent này có khả năng truy cập vào một bộ công cụ (toolkit) để quản lý lịch sử hội thoại và tạo ra các câu trả lời mạch lạc, có ngữ cảnh thông qua API venice.ai.
 
Kiến trúc cốt lõi
 
Mô hình sẽ bao gồm 3 thành phần chính của LangChain:
Agent Executor: "Bộ não" điều phối, nhận yêu cầu từ người dùng và quyết định sử dụng Tool nào dựa trên prompt và ngữ cảnh.
Toolkit: Một bộ các công cụ (Tools) được định nghĩa sẵn, mỗi công cụ thực hiện một chức năng cụ thể (gọi API, đọc/ghi DB).
Memory: Cơ chế lưu trữ và truy xuất lịch sử hội thoại, tích hợp trực tiếp vào Agent để cung cấp ngữ cảnh.
 
Phân tích Lựa chọn Cơ sở dữ liệu (DB)
 
Để lưu trữ lịch sử tin nhắn, chúng ta cần một DB đáp ứng các yêu cầu: ghi (append) nhanh và đọc N tin nhắn cuối cùng (read last N) hiệu quả.
Lựa chọn 1: Key-Value Store (ví dụ: Redis)
Ưu điểm: Tốc độ cực cao. Các lệnh như LPUSH (thêm vào đầu danh sách) và LRANGE (lấy một khoảng của danh sách) trong Redis được thiết kế hoàn hảo cho việc quản lý lịch sử chat. Rất dễ triển khai cho PoC.
Nhược điểm: Khó thực hiện các truy vấn phức tạp nếu sau này có nhu cầu.
Lựa chọn 2: Document DB (ví dụ: MongoDB)
Ưu điểm: Linh hoạt, lưu tin nhắn dưới dạng document (JSON) rất tự nhiên.
Nhược điểm: Cấu hình phức tạp hơn Redis một chút.
Lựa chọn 3: Relational DB (ví dụ: PostgreSQL)
Ưu điểm: Bền vững, đáng tin cậy.
Nhược điểm: Overkill (quá mức cần thiết) cho bài toán đơn giản là lưu và đọc lịch sử chat.
=> Khuyến nghị: Sử dụng Redis. Đây là lựa chọn tối ưu cho giai đoạn đầu vì tốc độ và sự tương thích hoàn hảo với các tác vụ ghi cuối, đọc N cuối mà các tool của chúng ta yêu cầu.
 
2. Đề Xuất Kiến Trúc Agent & Tools
 
Chúng ta sẽ xây dựng các thành phần sau bằng LangChain.
 
1. Agent Core (Agent Executor)
 
Sử dụng một agent có khả năng function-calling (ví dụ: OpenAIFunctionsAgent hoặc tương đương nếu venice.ai hỗ trợ) để agent có thể gọi các tool một cách đáng tin cậy.
Agent sẽ được cung cấp một "system prompt" để hướng dẫn nó cách sử dụng các tool để trả lời người dùng. Ví dụ: "Bạn là một trợ lý trò chuyện. Hãy sử dụng các tool có sẵn để tra cứu lịch sử và trả lời người dùng một cách tự nhiên."
 
2. LangChain Memory Component
 
Thay vì tạo tool get_history thủ công, chúng ta sẽ tận dụng các module Memory có sẵn của LangChain để tích hợp trực tiếp vào agent.
Bắt đầu với ConversationBufferWindowMemory: Module này tự động quản lý việc chỉ giữ lại k tin nhắn cuối cùng trong bộ nhớ, khớp chính xác với yêu cầu "get N tin nhắn gần nhất".
Nâng cao với ConversationSummaryBufferMemory: Module này kết hợp việc giữ lại k tin nhắn cuối và tự động tóm tắt các tin nhắn cũ hơn, khớp với yêu cầu summary.
 
3. Toolkit (Danh sách các Tool tùy chỉnh)
 
Đây là các hàm Python được đóng gói thành Tool object trong LangChain.
Tool 1: generate_venice_message
Chức năng: Gói lệnh gọi API đến venice.ai.
Đầu vào: user_query: str, character_id: str. Lịch sử chat sẽ được Agent tự động đưa vào prompt.
Đầu ra: ai_response: str.
Tool 2: save_message_to_history
Chức năng: Lưu một tin nhắn (của user hoặc AI) vào Redis. Agent sẽ gọi tool này sau mỗi lượt hội thoại để cập nhật lịch sử.
Đầu vào: session_id: str, message_content: str, message_type: str ('user' hoặc 'ai').
Đầu ra: status: str (ví dụ: "Lưu thành công").
Tool 3: summarize_long_history
Chức năng: Khi cần, agent có thể chủ động gọi tool này để tóm tắt một đoạn hội thoại dài. Tool này sẽ đọc lịch sử từ Redis và gọi lại venice.ai với một prompt chuyên để tóm tắt.
Đầu vào: session_id: str.
Đầu ra: summary_text: str.)

task tôi : Tạo một AI Agent khác (dùng để demo) - có chức năng chat với người dùng (chat kiểu gì cũng được). Nghiên cứu phần tóm tắt cuộc trò chuyện và truyền lịch sử của cuộc trò chuyện vào mỗi tin nhắn (ưu tiên dùng redis)