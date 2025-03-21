# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import datetime
import pytz
import requests
import json
# Base URL của API (thay bằng URL thực tế khi triển khai)
API_BASE_URL = "http://demo2.ninavietnam.org/chatbot/search.php"

    
#Action lấy giờ hiện tại
class ActionGetTimeCurrent(Action):
    def name(self) -> str:
        return "action_get_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        
        vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        vietnam_time = datetime.datetime.now(vietnam_tz)
        dispatcher.utter_message("Bây giờ là "+vietnam_time.strftime("%H:%M")+" (Theo múi giờ "+vietnam_time.strftime("%Z")+")" )

# Action reset các slot liên quan đến tìm kiếm
class ActionResetSearchSlots(Action):
    def name(self):
        return "action_reset_search_slots"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # Reset các slot liên quan đến tìm kiếm sản phẩm về None
        return [
            SlotSet("product", None),
            SlotSet("color", None),
            SlotSet("price", None),
            SlotSet("category", None),
            SlotSet("size", None),
            SlotSet("brand", None),
            SlotSet("quantity", None)
            
        ]
    
#Tìm sản phẩm     
class ActionSearchProduct(Action):
    def name(self):
        return "action_search_product"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
       # Lấy entities từ câu hiện tại
        current_entities = tracker.latest_message.get("entities", [])
        entity_dict = {entity["entity"]: entity["value"] for entity in current_entities}

        # Lấy giá trị từ entities hiện tại
        product = entity_dict.get("product")
        color = entity_dict.get("color")
        price = entity_dict.get("price")
        category = entity_dict.get("category")
        size = entity_dict.get("size")
        brand = entity_dict.get("brand")
        quantity = entity_dict.get("quantity")

        # Kiểm tra giá trị slot và xây dựng phản hồi
        if not product:
            response = "Tôi không hiểu bạn muốn tìm sản phẩm nào. Bạn có thể nói rõ hơn không?"
        else:
            response = f"Tôi đang tìm {product}"
            if color:
                response += f" màu {color}"
            if price:
                response += f" có giá {price}"
            if size:
                response += f" có kích thước {size}"
            if brand:
                response += f" thuộc thương hiệu {brand}"
            if category:
                response += f" thuộc danh mục {category}"
            response += ". Bạn đợi một chút nhé!"

        # Gửi phản hồi
        dispatcher.utter_message(text=response)



        # Xây dựng URL API với các tham số
        base_url = API_BASE_URL
        params = {
            "keyword": product if product else "",
            "size": size if size else "",
            "color": color if color else "",
            "brand": brand if brand else "",
            "category": category if category else ""
        }

        try:
            # Gửi request tới API
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Kiểm tra lỗi HTTP

            # Parse dữ liệu JSON trả về
            products = response.json()

            # Kiểm tra nếu không có sản phẩm nào
            if not products:
                dispatcher.utter_message(text="Không tìm thấy sản phẩm nào phù hợp.")
                return []

            # Tạo phản hồi sinh động
            message = "Tôi đã tìm thấy các sản phẩm sau:\n\n"
            for product in products:
                name = product.get("name", "Không rõ tên")
                size = product.get("size", "Không rõ kích thước")
                color = product.get("color", "Không rõ màu")
                brand = product.get("brand", "Không rõ thương hiệu")
                price = "{:,}".format(product.get("price", 0)).replace(",", ".")
                image = product.get("image", "")

               

                # Định dạng Markdown + HTML cho giá màu đỏ
                product_info = (
                    f"![{name}]({image})\n"
                    f"**{name}**\n"
                    f"**{price} VNĐ**\n"
                    f"Kích thước: {size} | Màu: {color} | Thương hiệu: {brand}\n"
                )
                
            message += product_info + "---\n"
            dispatcher.utter_message(text=message)

        except requests.exceptions.RequestException as e:
            # Xử lý lỗi khi gọi API
            dispatcher.utter_message(text=f"Có lỗi xảy ra khi tìm kiếm sản phẩm: {str(e)}")
        except json.JSONDecodeError:
            # Xử lý lỗi khi parse JSON
            dispatcher.utter_message(text="Dữ liệu trả về từ server không hợp lệ.")


        # Cập nhật slot từ entities hiện tại
        return [
            SlotSet("product", product),
            SlotSet("color", color),
            SlotSet("price", price),
            SlotSet("category", category),
            SlotSet("size", size),
            SlotSet("brand", brand),
            SlotSet("quantity", quantity)
        ]