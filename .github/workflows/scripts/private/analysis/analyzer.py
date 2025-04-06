
bvid = os.getenv('INPUT_BVID', '')from bilibili_api import video, comment, sync, Credential
from bilibili_api import video, comment, sync, Credential
import pandas as pd
import time

#登录凭证
credential = Credential(
    sessdata="8c41d7b3%2C1759376163%2C0276e%2A42CjB0YHqI0jveT3mFBw1HFIebNzl6PjLI6qUa1hiAP8vpMDzR_OSm165dAuhD2QQhoZwSVktsamdjT0lUMGZLb2hHQjY3cU5xdEwwTm1GYVVxMmw0dHRqbHpCb1U5dm1CVjFMZ3N1X3g4U0tLanptc25vT2E2Qy1VdGo2c0NST0lsMVNzdzlwdmpnIIEC",
    bili_jct="6dbd103f6068d9d2a69cac8ac5fd5a70",
    buvid3="C95FBCB1-EE6F-4902-7A0E-C578F5587D1684942infoc"
)

inputbvid = input("请输入视频bvid")
#获取视频aid（oid）
v = video.Video(bvid=inputbvid, credential=credential)
aid = v.get_aid()

# 获取评论
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


df = pd.DataFrame([{
    "用户": c['member']['uname'],
    "内容": c['content']['message'],
    "时间": pd.to_datetime(c['ctime'], unit='s'),
    "点赞数": c['like'],
    "IP属地": c.get('reply_control', {}).get('location', '未知')
} for c in all_comments])

df.to_csv("b站评论.csv", index=False, encoding='utf_8_sig')


from snownlp import SnowNLP
import pandas as pd
import time

# 1. 读取爬取的B站评论数据（假设原爬虫输出为b站评论.csv）
input_path = "./b站评论.csv"
df = pd.read_csv(input_path, encoding='utf_8_sig')

# 2. 情感分析处理函数
def analyze_sentiment(row):
    try:
        s = SnowNLP(row['内容'])
        # 调整阈值：0.7+积极，0.3-消极，中间中性
        sentiment = "积极" if s.sentiments > 0.7 else ("消极" if s.sentiments < 0.3 else "中性")
        return pd.Series([s.sentiments, sentiment])
    except Exception as e:
        print(f"分析失败：{row['内容'][:20]}... 错误：{str(e)}")
        return pd.Series([None, "解析错误"])

# 3. 应用情感分析（进度可视化）
print("开始情感分析...")
start_time = time.time()
df[['情感得分', '情感分类']] = df.apply(analyze_sentiment, axis=1)
print(f"分析完成，耗时 {time.time()-start_time:.2f} 秒")

# 4. 保存结果（新增情感列，保留原爬虫所有字段）
output_path = "./b站评论_情感分析结果.csv"
df.to_csv(output_path, index=False, encoding='utf_8_sig')
print(f"结果已保存至 {output_path}")



import pandas as pd
import numpy as np
from wordcloud import WordCloud
from PIL import Image
import jieba
import jieba.posseg as pseg
from collections import Counter
import matplotlib.pyplot as plt

# 1. 数据加载与清洗
df = pd.read_csv("./b站评论_情感分析结果.csv", encoding='utf_8_sig')
df['内容'] = df['内容'].astype(str).str.replace(r'\[.*?\]', '', regex=True)  # 去除表情符号

# 2. 中文停用词增强
stopwords = set(["这个", "那个", "真的", "感觉", "就是", "什么", "视频", "up主", "哈哈哈",
                 "啊啊啊", "硬币", "弹幕", "一键三连", "哈哈哈", "啊啊啊"])


# 3. 词频统计（优化版）
def get_word_freq(texts, use_pos_weight=True):
    words = []
    for text in texts:
        if use_pos_weight:
            # 带词性权重的分词
            for word, flag in pseg.lcut(text):
                if len(word) > 1 and word not in stopwords:
                    weight = 3 if flag.startswith('a') else 2 if flag.startswith(('v', 'n')) else 1
                    words.extend([word] * weight)
        else:
            # 普通分词
            words.extend([w for w in jieba.lcut(text) if len(w) > 1 and w not in stopwords])
    return Counter(words)


# 4. 安全生成词云
def safe_generate_wc(freq_dict, **kwargs):
    """处理词频为空的情况"""
    if not freq_dict:
        print("警告：词频字典为空，生成示例词云")
        freq_dict = {"无有效数据": 1}
    return WordCloud(**kwargs).generate_from_frequencies(freq_dict)


# 5. 主流程（只生成负面词云）
try:
    # 只获取负面评论
    neg_texts = df[df['情感分类'] == '消极']['内容'].dropna().tolist()

    # 获取词频
    neg_freq = get_word_freq(neg_texts)

    # 创建画布
    plt.figure(figsize=(10, 8), facecolor='white')

    # 设置中文字体（非常重要）
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 或者 'SimHei'
    plt.rcParams['axes.unicode_minus'] = False

    # 生成负面词云
    neg_wc = safe_generate_wc(
        neg_freq,
        font_path="msyh.ttc",  # 确保这个字体文件存在，或者使用系统自带的中文字体
        background_color="white",
        colormap="Reds",
        width=1000,
        height=600,
        max_words=200,
        collocations=False
    )

    plt.imshow(neg_wc, interpolation="bilinear")
    plt.title("B站负面评论关键词分析", fontsize=18, pad=20)
    plt.axis("off")

    # 保存输出
    output_path = "./负面情绪词云.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"负面词云已保存到: {output_path}")
    plt.show()

except Exception as e:
    print(f"生成词云时出错: {str(e)}")
    # 生成错误提示图
    plt.figure(figsize=(10, 5))
    plt.text(0.5, 0.5, "词云生成失败\n请检查数据格式", ha='center', va='center', fontproperties='Microsoft YaHei')
    plt.axis('off')
    plt.savefig("词云错误提示.png")


from plotly import graph_objects as go
import pandas as pd

# 数据加载与预处理
try:
    df = pd.read_csv("./b站评论_情感分析结果.csv", encoding='utf_8_sig')

    # 确保时间列转换为datetime类型
    df['时间'] = pd.to_datetime(df['时间'])

    # 筛选负面评论并设置时间索引
    negative_df = df[df['情感分类'] == '消极'].copy()
    negative_df = negative_df.set_index('时间')  # 关键修正：将时间列设为索引

except Exception as e:
    print(f"数据加载失败: {str(e)}")
    exit()


time_span = negative_df.index.max() - negative_df.index.min()
if time_span > pd.Timedelta(days=3):  # 数据跨度>3天用4小时窗口
    bin_size = '4H'
elif time_span > pd.Timedelta(days=1):  # 1-3天用2小时窗口
    bin_size = '2H'
else:  # 小于1天用1小时窗口
    bin_size = '1H'

hourly_counts = negative_df.resample(bin_size).size()  # 现在可以正确resample

# 创建交互图表
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=hourly_counts.index,
    y=hourly_counts.values,
    mode='lines+markers',
    line=dict(color='#e63946', width=2),
    marker=dict(size=6, color='#1d3557'),
    name=f'负面评论（{bin_size}窗口）',
    hovertemplate='时间: %{x|%m-%d %H:%M}<br>数量: %{y}'
))

# 智能标注（仅标注超过平均值的峰值）
mean_count = hourly_counts.mean()
peaks = hourly_counts[hourly_counts > 1.5 * mean_count]
for time, count in peaks.items():
    fig.add_annotation(
        x=time,
        y=count,
        text=f"{count}",
        showarrow=True,
        arrowhead=3,
        ax=0,
        ay=-30,
        bgcolor="rgba(255,255,255,0.7)"
    )

# 5. 图表布局优化
fig.update_layout(
    title=dict(
        text='<b>B站负面评论动态趋势</b>',
        x=0.5,
        font=dict(size=18)
    ),
    xaxis=dict(
        title='时间',
        rangeslider=dict(visible=True),
        type='date'
    ),
    yaxis=dict(title='评论量'),
    hoverlabel=dict(
        bgcolor="white",
        font_size=12
    ),
    template='plotly_white',
    height=600
)

# 6. 保存和显示
output_file = "./B站负面评论_交互式.html"
fig.write_html(output_file, auto_open=True)
print(f"交互图表已保存至: {output_file}")


# import pandas as pd
# import numpy as np
# import plotly.express as px
# from datetime import datetime

# df = pd.read_csv('./b站评论_情感分析结果.csv', encoding='utf_8_sig')

# # 转换时间列
# df['时间'] = pd.to_datetime(df['时间'])
# df['日期'] = df['时间'].dt.date

# # 提取省份信息
# def extract_province(ip):
#     if pd.isna(ip) or ip == '未知':
#         return "未知"
#     # 处理格式："IP属地：广东" → "广东"
#     province = str(ip).split('：')[-1].strip()

#     if province.endswith(('北京', '上海', '天津', '重庆', '香港', '澳门')):
#         return province[-2:]  # 取最后两个字
#     return province[:2]  # 其他省份取前两个字

# df['省份'] = df['IP属地'].apply(extract_province)


# negative_df = df[df['情感分类'] == '消极']
# daily_counts = negative_df.groupby(['日期', '省份']).size().reset_index(name='负面评论数')


# province_coords = {
#     '北京': (116.4074, 39.9042),
#     '上海': (121.4737, 31.2304),
#     '天津': (117.1994, 39.0851),
#     '重庆': (106.5505, 29.5630),
#     '安徽': (117.2830, 31.8612),
#     '福建': (119.3062, 26.0753),
#     '甘肃': (103.8342, 36.0610),
#     '广东': (113.2644, 23.1291),
#     '广西': (108.3200, 22.8240),
#     '贵州': (106.7074, 26.5982),
#     '海南': (110.1999, 20.0442),
#     '河北': (114.5025, 38.0455),
#     '河南': (113.6654, 34.7579),
#     '黑龙江': (126.6425, 45.7569),
#     '湖北': (114.2986, 30.5843),
#     '湖南': (112.9823, 28.1941),
#     '吉林': (125.3245, 43.8868),
#     '江苏': (118.7674, 32.0415),
#     '江西': (115.8922, 28.6765),
#     '辽宁': (123.4291, 41.7968),
#     '内蒙古': (111.7510, 40.8413),
#     '宁夏': (106.2588, 38.4712),
#     '青海': (101.7800, 36.6232),
#     '山东': (117.0211, 36.6758),
#     '山西': (112.5492, 37.8570),
#     '陕西': (108.9480, 34.2632),
#     '四川': (104.0657, 30.6595),
#     '西藏': (91.1172, 29.6469),
#     '新疆': (87.6168, 43.8256),
#     '云南': (102.7123, 25.0406),
#     '浙江': (120.1536, 30.2875),
#     '香港': (114.1694, 22.3193),
#     '澳门': (113.5491, 22.1987),
#     '台湾': (121.5201, 25.0300),
#     '内蒙古自治区': (111.7510, 40.8413),
#     '广西壮族自治区': (108.3200, 22.8240),
#     '西藏自治区': (91.1172, 29.6469),
#     '新疆维吾尔自治区': (87.6168, 43.8256)
# }

# # 确保所有省份都有坐标
# valid_provinces = [p for p in daily_counts['省份'].unique() if p in province_coords]
# daily_counts = daily_counts[daily_counts['省份'].isin(valid_provinces)]


# all_dates = pd.date_range(daily_counts['日期'].min(), daily_counts['日期'].max())
# full_index = pd.MultiIndex.from_product(
#     [all_dates, valid_provinces],
#     names=['日期', '省份']
# )
# daily_counts = daily_counts.set_index(['日期', '省份']).reindex(full_index, fill_value=0).reset_index()

# #  添加坐标数据
# daily_counts['经度'] = daily_counts['省份'].map(lambda x: province_coords[x][0])
# daily_counts['纬度'] = daily_counts['省份'].map(lambda x: province_coords[x][1])

# #生成动态热力图
# fig = px.scatter_geo(
#     daily_counts,
#     lat='纬度',
#     lon='经度',
#     size=np.log1p(daily_counts['负面评论数'] + 1) * 10,  # 对数缩放，+1避免log(0)
#     color='负面评论数',
#     animation_frame='日期',
#     hover_name='省份',
#     hover_data={'负面评论数': True, '日期': False, '经度': False, '纬度': False},
#     scope='asia',
#     title='B站负面评论地域动态分布',
#     color_continuous_scale='reds',
#     range_color=[0, daily_counts['负面评论数'].quantile(0.9)],  # 避免极端值影响
#     size_max=30  # 控制最大气泡大小
# )
# fig.update_geos(
#     center={'lat': 35, 'lon': 105},  # 地图中心（中国）
#     projection_scale=4,  # 缩放级别
#     landcolor='lightgray',  # 背景色
#     coastlinecolor='gray',  # 海岸线颜色
# )

# #  添加播放控件
# fig.update_layout(
#     updatemenus=[{
#         "buttons": [{
#             "args": [None, {"frame": {"duration": 1000}}],
#             "label": "播放",
#             "method": "animate",
#         }],
#     }],
#     # 确保所有点都显示
#     geo=dict(
#         showland=True,
#         landcolor='rgb(243, 243, 243)',
#         countrycolor='rgb(204, 204, 204)',
#     )
# )


# fig.write_html('B站负面评论动态分布.html', auto_open=True)
# fig.show()
