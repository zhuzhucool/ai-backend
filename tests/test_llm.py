from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=None,  # 会自动从环境变量里读 OPENAI_API_KEY
    base_url="https://api.deepseek.com/v1",
)

def main():
    try:
        resp = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "你好，测试一下连接。"},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        print("调用成功")
        print(resp.choices[0].message.content)

    except Exception as e:
        print("调用失败")
        print(type(e).__name__)
        print(e)

if __name__ == "__main__":
    main()
