async function analyze() {
  try {
    const bvid = document.getElementById('bvid-input').value.trim();
    
    // 改用更可靠的代理端点（示例）
    const response = await fetch('https://api.your-proxy.com/trigger', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-Source': 'bili-analysis-web' // 自定义标识
      },
      body: JSON.stringify({ bvid })
    });

    if (!response.ok) {
      throw new Error(`API返回错误: ${response.status}`);
    }
    
    // 轮询结果时添加重试机制
    await pollWithRetry(bvid);
    
  } catch (error) {
    console.error('完整错误日志:', error);
    showError(`分析失败: ${error.message}`);
  }
}

// 带重试的轮询函数
async function pollWithRetry(bvid, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await fetch(`/results/${bvid}.json`);
      if (result.ok) return await result.json();
    } catch (e) {
      if (i === maxRetries - 1) throw e;
      await new Promise(r => setTimeout(r, 2000 * (i + 1)));
    }
  }
}
