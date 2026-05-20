import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime


def curl_webpage(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    follow_redirects: bool = True
) -> Dict[str, Any]:
    """
    通过HTTP请求访问网页并返回网页内容
    
    Args:
        url: 要访问的URL地址
        method: HTTP方法 (GET, POST, PUT, DELETE等)
        headers: 请求头字典
        params: URL查询参数
        data: 表单数据
        json_data: JSON数据
        timeout: 超时时间（秒）
        follow_redirects: 是否跟随重定向
    
    Returns:
        包含响应信息的字典
    """
    if not url:
        return {
            "success": False,
            "error": "URL不能为空"
        }
    
    if not url.startswith(('http://', 'https://')):
        return {
            "success": False,
            "error": "URL必须以http://或https://开头"
        }
    
    try:
        start_time = time.time()
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json_data,
            timeout=timeout,
            allow_redirects=follow_redirects
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        result = {
            "success": True,
            "url": url,
            "method": method.upper(),
            "status_code": response.status_code,
            "status_reason": response.reason,
            "elapsed_time": round(elapsed_time, 3),
            "headers": dict(response.headers),
            "content_length": len(response.content),
            "content_type": response.headers.get('Content-Type', 'unknown'),
            "encoding": response.encoding,
            "final_url": response.url,
            "redirect_history": [r.url for r in response.history] if response.history else []
        }
        
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            try:
                result["content_type_category"] = "json"
                result["content"] = response.json()
                result["content_preview"] = str(response.json())[:500]
            except Exception:
                result["content_type_category"] = "text"
                result["content"] = response.text
                result["content_preview"] = response.text[:500]
        elif 'text/' in content_type:
            result["content_type_category"] = "text"
            result["content"] = response.text
            result["content_preview"] = response.text[:500]
        else:
            result["content_type_category"] = "binary"
            result["content"] = f"<二进制数据，大小: {len(response.content)} 字节>"
            result["content_preview"] = f"<二进制数据，前100字节: {response.content[:100]}>"
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": f"请求超时（{timeout}秒）",
            "url": url
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"连接错误: {str(e)}",
            "url": url
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"请求异常: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}",
            "url": url
        }


def curl_get(url: str, **kwargs) -> Dict[str, Any]:
    """
    发送GET请求的便捷方法
    
    Args:
        url: 要访问的URL地址
        **kwargs: 其他参数传递给curl_webpage
    
    Returns:
        包含响应信息的字典
    """
    return curl_webpage(url, method="GET", **kwargs)


def curl_post(url: str, **kwargs) -> Dict[str, Any]:
    """
    发送POST请求的便捷方法
    
    Args:
        url: 要访问的URL地址
        **kwargs: 其他参数传递给curl_webpage
    
    Returns:
        包含响应信息的字典
    """
    return curl_webpage(url, method="POST", **kwargs)


def get_weather_forecast(city: str) -> Dict[str, Any]:
    """
    获取指定城市的天气预报
    
    Args:
        city: 城市名称
    
    Returns:
        包含天气预报信息的字典
    """
    url = f"https://wttr.in/{city}"
    return curl_get(url)


if __name__ == "__main__":
    import json
    
    print("网络访问工具函数")
    print("=" * 60)
    
    # 天气查询功能
    city = input("请输入城市名称（例如：北京、上海、广州）: ")
    print(f"\n获取{city}的天气预报...")
    result = get_weather_forecast(city)
    
    if result.get('success'):
        print(f"状态码: {result.get('status_code')}")
        print(f"耗时: {result.get('elapsed_time')}秒")
        print("\n天气预报:\n")
        print(result.get('content', ''))
    else:
        print(f"获取天气失败: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("操作完成！")
