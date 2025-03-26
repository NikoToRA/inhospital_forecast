import os
import uvicorn
import subprocess
import logging
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles

# ロギング設定をインポート
try:
    from logging_config import logger
except ImportError:
    # ロギング設定が見つからない場合は基本設定を使用
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

app = FastAPI()

# Streamlitを起動するサブプロセス
streamlit_process = None
STREAMLIT_PORT = 8501

@app.on_event("startup")
async def startup_event():
    global streamlit_process
    
    # Azure環境かどうかを確認
    is_azure = bool(os.environ.get('WEBSITE_SITE_NAME'))
    logger.info(f"アプリケーション起動: Azure環境 = {is_azure}")
    
    # Streamlitコマンドの設定
    streamlit_cmd = ["streamlit", "run", "app.py", 
                    "--server.port", str(STREAMLIT_PORT), 
                    "--server.headless", "true",
                    "--browser.serverAddress", "0.0.0.0",
                    "--server.enableCORS", "false",
                    "--browser.gatherUsageStats", "false"]
    
    logger.info(f"Streamlit起動コマンド: {' '.join(streamlit_cmd)}")
    
    # Streamlitを別プロセスで起動
    try:
        streamlit_process = subprocess.Popen(streamlit_cmd)
        logger.info(f"Streamlit起動成功 (PID: {streamlit_process.pid})")
    except Exception as e:
        logger.error(f"Streamlit起動失敗: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    global streamlit_process
    if streamlit_process:
        logger.info(f"Streamlitプロセス終了 (PID: {streamlit_process.pid})")
        streamlit_process.terminate()

@app.get("/", response_class=RedirectResponse)
async def root():
    """ルートパスへのアクセスをStreamlitにリダイレクト"""
    logger.info("ルートパスへのアクセス - Streamlitにリダイレクト")
    return RedirectResponse(url="/streamlit")

@app.get("/streamlit{path:path}")
async def streamlit_proxy(request: Request, path: str):
    """Streamlitへのプロキシ"""
    url = f"http://localhost:{STREAMLIT_PORT}{path}"
    logger.info(f"Streamlitプロキシ: {url}")
    
    # パスからクエリパラメータを抽出
    query_string = request.url.query
    if query_string:
        url = f"{url}?{query_string}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        async with httpx.AsyncClient() as client:
            method = request.method
            if method == "GET":
                streamlit_response = await client.get(url, headers=headers, follow_redirects=True)
            elif method == "POST":
                body = await request.body()
                streamlit_response = await client.post(url, headers=headers, content=body, follow_redirects=True)
            else:
                return Response(content="Method not supported", status_code=405)
                
            content = streamlit_response.content
            status_code = streamlit_response.status_code
            response_headers = dict(streamlit_response.headers)
            
            # StreamlitのCSSとJavaScriptで相対パスを修正
            if "text/html" in response_headers.get("content-type", ""):
                content = content.replace(b'href="/', b'href="/streamlit/')
                content = content.replace(b'src="/', b'src="/streamlit/')
                
            return Response(
                content=content,
                status_code=status_code,
                headers=response_headers
            )
    except Exception as e:
        logger.error(f"Streamlitプロキシエラー: {str(e)}")
        return Response(
            content=f"Error connecting to Streamlit: {str(e)}",
            status_code=500
        )

@app.get("/healthcheck")
async def healthcheck():
    logger.info("ヘルスチェックリクエスト受信")
    # Streamlitプロセスの状態を確認
    if streamlit_process and streamlit_process.poll() is None:
        # Streamlitの応答も確認
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:{STREAMLIT_PORT}/healthz")
                if response.status_code == 200:
                    return {"status": "healthy", "streamlit": "running and responding"}
                else:
                    return {"status": "unhealthy", "streamlit": "running but not responding"}
        except:
            return {"status": "unhealthy", "streamlit": "running but not responding"}
    else:
        return {"status": "unhealthy", "streamlit": "not running"}

# メインのAzure Web Appエントリポイント
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"ASGIアプリケーション起動: port={port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 