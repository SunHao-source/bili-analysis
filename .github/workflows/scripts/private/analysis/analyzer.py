from bilibili_api import video, comment, sync, Credential
import pandas as pd
import time
from snownlp import SnowNLP
import jieba
import jieba.posseg as pseg
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. 初始化配置
def init_config():
    """加载环境变量和凭证"""
    return Credential(
        sessdata=os.getenv('BILI_SESSDATA', ''),
        bili_jct=os.getenv('BILI_JCT', ''),
        buvid3=os.getenv('BILI_BUVID3', '')
    )

# 2. 数据采集模块
def fetch_comments(bvid, credential):
    """获取B站视频评论"""
    v = video.Video(bvid=bvid, credential=credential)
    aid = v.get_aid()
    
    all_comments = []
    page = 1
    while True:
        try:
            data = sync(comment.get_comments(
                oid=aid,
                type_=comment.CommentResourceType.VIDEO,
                page_index=page,
                credential=credential
            ))
            if not data['replies']:
                break
                
            all_comments.extend(data['replies'])
            print(f"已爬取第{page}页，共{len(data['replies'])}条评论")
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"第{page}页爬取失败: {str(e)}")
            break
    
    return pd.DataFrame([{
        "用户": c['member']['uname'],
        "内容": c['content']['message'],
        "时间": pd.to_datetime(c['ctime'], unit='s'),
        "点赞数": c['like'],
        "IP属地": c.get('reply_control', {}).get('location', '未知')
    } for c in all_comments])

# 3. 情感分析模块
def analyze_sentiment(df):
    """执行情感分析"""
    def _analyze(row):
        try:
            s = SnowNLP(row['内容'])
            return "积极" if s.sentiments > 0.7 else ("消极" if s.sentiments < 0.3 else "中性")
        except:
            return "解析错误"
    
    print("开始情感分析...")
    df['情感分类'] = df['内容'].apply(_analyze)
    return df

# 4. 可视化模块
def generate_visualizations(df):
    """生成所有可视化结果"""
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 生成词云
    generate_wordcloud(df)
    
    # 生成趋势图
    generate_trend_chart(df)
    
    # 生成热力图
    generate_heatmap(df)

def generate_wordcloud(df):
    """生成负面评论词云"""
    stopwords = set(["这个", "那个", "视频", "up主", "哈哈哈"])
    neg_texts = df[df['情感分类'] == '消极']['内容'].astype(str)
    
    words = []
    for text in neg_texts:
        for word, flag in pseg.lcut(text.replace('[', '').replace(']', '')):
            if len(word) > 1 and word not in stopwords:
                words.append(word)
    
    if not words:
        words = ["无有效数据"]
        
    wc = WordCloud(
        font_path='msyh.ttc',
        width=800,
        height=600,
        background_color='white'
    ).generate(' '.join(words))
    
    plt.figure(figsize=(10, 8))
    plt.imshow(wc)
    plt.axis("off")
    plt.savefig('output/wordcloud.png', bbox_inches='tight')
    plt.close()

def generate_trend_chart(df):
    """生成负面评论趋势图"""
    df['时间'] = pd.to_datetime(df['时间'])
    negative_df = df[df['情感分类'] == '消极'].set_index('时间')
    hourly_counts = negative_df.resample('4H').size()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly_counts.index,
        y=hourly_counts.values,
        mode='lines+markers'
    ))
    fig.write_html('output/trend.html')

def generate_heatmap(df):
    """生成地域热力图"""
    province_coords = {
        '北京': (116.40, 39.90),
        '上海': (121.47, 31.23),
        '广东': (113.26, 23.12),
        # 其他省份坐标...
    }
    
    df['省份'] = df['IP属地'].str.split('：').str[-1].str[:2]
    daily_counts = df[df['情感分类'] == '消极'].groupby(['时间', '省份']).size().reset_index(name='负面评论数')
    
    fig = px.scatter_geo(
        daily_counts,
        lat='纬度',
        lon='经度',
        size='负面评论数',
        animation_frame='时间'
    )
    fig.write_html('output/heatmap.html')

# 5. 主执行流程
def main():
    # 从环境变量获取BV号（GitHub Actions传入）
    bvid = os.getenv('INPUT_BVID', '')
    if not bvid:
        bvid = input("请输入视频BV号: ").strip()
    
    credential = init_config()
    
    # 执行全流程
    comments_df = fetch_comments(bvid, credential)
    analyzed_df = analyze_sentiment(comments_df)
    analyzed_df.to_csv('output/comments_analyzed.csv', index=False)
    
    generate_visualizations(analyzed_df)
    print("分析完成！结果保存在output目录")

if __name__ == "__main__":
    main()
