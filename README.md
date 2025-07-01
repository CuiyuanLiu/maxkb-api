# maxkb-api
This project is to show how to send the api out once you encountered an issue that base_url is not working. In this
project the output is given in openai format (used for open-webui, you may change to your own format).

To get chatting with MaxKB through API, you need to create an API-key first, which could be done in your dashbroad,
![image](https://github.com/user-attachments/assets/6726be70-56a4-4054-b8a1-f2a70be37904)
Notes that, kindly leave the CORS field empty to avoid any CORS issue while getting API-KEY.

Then, go to the API document and get the application_id and chat_id step by step, only with chat_id you could contact
with the MaxKB using API. For a more detailed maxkb tutorial, please refer to the below website:
[https://maxkb.cn/docs/](https://maxkb.cn/docs/dev_manual/APIKey_chat/)

I provided both text response and stream response to choose, to use this API you need to first update your paras in
`paras.py`, which means input your application_id and your model_id there:
```python
# Modify your parameter here.
class MaxKBParas():
    input_url="http://127.0.0.1:8080/api/application"
    application_id="Your-Application-ID=Here"
    apikey="Your-APIKEY-here"
    port=2000
    model_id="Your Model Name here"
```

Then kindly use `python api.py` to run so.  

Thank you so much for your kind reading.
