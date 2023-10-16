# ライブラリインポート
import streamlit as st
import sqlite3
import requests
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
import json
import matplotlib.pyplot as plt #グラフ描画ライブラリ
import japanize_matplotlib # matplotlib日本語化対応ライブラリ
import seaborn as sns
from PIL import Image
from geopy.distance import geodesic
import re
import urllib.request
import folium #地図機能

# DB読み込み
conn = sqlite3.connect('STEP3チーム課題_TA_IndéMode_DB.db') # DB(SQLite)接続
# SQLクエリ実行してデータフレーム化
query1 = 'SELECT * FROM "都内利用者数上位駅";'  
query2 = 'SELECT * FROM "東京23区賃料(募集金額)相場目安ランキングfrom飲食店ドットコム";'  
query3 = 'SELECT * FROM "東京23区スクレイピングコード一覧";'  
query4 = 'SELECT * FROM "東京23区路線一覧_JRメトロ";' 
query5 = 'SELECT * FROM "東京23区駅一覧_JR東京メトロ";' 
query10 = 'SELECT * FROM "サロン利用実態";'   
df1 = pd.read_sql_query(query1, conn)
df2 = pd.read_sql_query(query2, conn)
df3 = pd.read_sql_query(query3, conn)
df4 = pd.read_sql_query(query4, conn)
df5 = pd.read_sql_query(query5, conn)
df10 = pd.read_sql_query(query10, conn)
conn.close()  # データベース接続閉じる

# リスト作成
line_list = df4['路線名']
station_list = df1['駅名']

# ここからstreamlitに表示される部分

# 1. アプリタイトル
st.title('IndéMode')
image0 = Image.open("image/salon-img.jpg")
st.image(image0, use_column_width=True)
st.subheader('自分のサロンを開こうとおもったら')
st.caption('条件を選択することで、あなたに最適な物件をレコメンドします')
st.write('') 

# 2. 入力用コード  
st.sidebar.write('下のグラフは 美容室の1日の平均来客数です。')
image1 = Image.open("image/美容室の平均客数.png")
st.sidebar.image(image1)

st.sidebar.write('下のグラフは 席数vs店舗面積 の開業実績です。')
image2 = Image.open("image/サロン開業実績_席数と店舗面積.png")
st.sidebar.image(image2)

st.sidebar.write('下の写真は内装費用の坪単価10万円、30万円のサロンイメージです。')
image3 = Image.open("image/内装イメージ.jpg")
st.sidebar.image(image3)

seat_count = st.sidebar.slider('Q1. ご開業されるサロンのカット席数を選択して下さい。', 1, 4, 8)

interior_cost = st.sidebar.slider('Q2. ご開業されるサロンの想定坪単価(万円)を選択して下さい。', 0, 10, 30)

stylist_count = st.sidebar.slider('Q3. ご開業されるサロンで雇用するスタイリストの人数を選択して下さい。', 1, 10, 1, 1)

turnover = st.sidebar.slider('Q4. ご開業されるサロンのカット席回転数 ( = 営業時間(h/日) / お客様1人あたりの施術時間(h/人) ) を選択して下さい。', 1, 12, 6, 1)

operationg_ratio = st.sidebar.slider('Q5. ご開業されるサロン想定稼働率を選択して下さい。※数値表示です。60%の場合は0.6を選択。)', 0.0, 1.0, 0.6, 0.01)

st.sidebar.write('下のグラフは スタイリストの年齢別給与です。')
image4 = Image.open("image/スタイリストの年齢別年収.png")
st.sidebar.image(image4)

stylist_salary = st.sidebar.slider('Q6. 雇用されるスタイリストの平均給与(万円/月)を選択して下さい。※雇用しない場合は「0」を選択して下さい。', 0, 10, 50, 1)

st.sidebar.write('下のグラフは女性客が1回の来店で使う金額の平均額です。')
image5 = Image.open("image/女性がサロンで使った金額.png")
st.sidebar.image(image5)

st.sidebar.write('下のグラフは男性客が1回の来店で使う金額の平均額です。')
image6 = Image.open("image/男性がサロンで使った金額.png")
st.sidebar.image(image6)

cut_price = st.sidebar.slider('Q7. ご開業されるサロンのお客様の客単価見込み(円)を選択して下さい。', 0, 20000, 8000, 100)/10000

st.sidebar.write('') 
st.sidebar.write('下のグラフは 首都圏駅の利用者数ランキングです。')
image7 = Image.open("image/首都圏駅_利用者数ランキング.png")
st.sidebar.image(image7)
station = st.sidebar.selectbox('Q8. どの駅の近くでご開業予定か教えて下さい。', station_list)
line = st.sidebar.selectbox('Q9. その駅の路線を教えて下さい。', line_list)

st.sidebar.write(f'まずは「 {line}{station} 駅」の周辺情報を調査します。')
st.sidebar.write('') 

# 仮の値を設定
#line = "JR山手線"
#station = "有楽町"

# 検索ボタン
if st.sidebar.button("検索実行"):
    # 検索ボタンが押された場合の処理
    st.sidebar.write("検索を開始します。")

    # heartrails.express APIで緯度経度、郵便番号を取得
    url = "https://express.heartrails.com/api/json?method=getStations&line=" + line + "&name=" + station
    response = requests.get(url)
    res = response.json()
    station_data = res.get('response', {}).get('station', [])


    base_url = "https://express.heartrails.com/api/json?method=getStations"
    params = {
        "line": line,
        "name": station
    }
    response = requests.get(base_url, params=params)
    res = response.json()
    station_data = res.get('response', {}).get('station', [])

    #print(response.url)  # レスポンス内容を確認
    #print(res)
    #print(station_data)


    # エリア調査関数
    def get_area_info(line, station):
        if station_data:
            # 最初の駅情報を取得
            first_station = station_data[0]
            station_longitude = first_station.get('x')
            station_latitude = first_station.get('y')
            station_postal = first_station.get('postal')
            # 郵便番号検索 APIで緯度経度を元に住所を取得
            postal_url = "https://zipcloud.ibsnet.co.jp/api/search?zipcode=" + station_postal
            postal_response = requests.get(postal_url)
            postal_res = postal_response.json()
            station_area = postal_res['results'][0].get('address2')   
            # 駅所在エリアの賃料相場を取得
            #display(df2.head(10))
            area_average_rent = str(df2[df2["区名"] == station_area][["平均額(円/坪)"]].values[0][0])
            # 駅所在エリアのサロン情報を取得
            # display(df3.head(10))
            area_code_rakuten =str(df3[df3["区名"] == station_area].values[0][1])
            # 情報格納のための空配列を用意
            s_name = []
            s_access = []
            s_price = []
            # HTML取得
            URL = 'https://beauty.rakuten.co.jp/addr' + area_code_rakuten + '/page{}/'
            # 複数ページ取得のためのループ処理
            for i in range(1,4):
                # 変数trget_urlに、アクセス先のURLを格納する
                saron_url = URL.format(i)
                # サーバー負荷低減のための1s待機
                sleep(1)
                # リクエスト
                saron_res = requests.get(saron_url)
                # 文字コード変換 (→ utf-8 )
                saron_res.encoding = 'utf-8'
                # BeautifulSoup(解析したいデータ,解析する方法)を指定し、soupに代入
                soup = BeautifulSoup(saron_res.text, "html.parser")
                # sectionデータ(1物件分データ)の取得
                property_section = soup.select('div.m-shopCard__headerContent')
                # property_sectionからsectionを1つずつ取り出してpsに代入
                for ps in property_section:
                    ps1 = ps.select('h3.m-shopCard__shopName')[0].text
                    ps2 = ps.select('li.m-shopCard__headerOutlineItem')[0].text.replace("アクセス：","")
                    ps3 = ps.select('li.m-shopCard__headerOutlineItem')[1].text.replace("カット単価：","").replace("～","").replace("￥","")
                    # それぞれ抽出したデータを配列に追加
                    s_name.append(ps1)
                    s_access.append(ps2)
                    s_price.append(ps3)
                # 物件数確認
                #print('サロン件数', len(s_name))
            # データ定義
            data_list = {
                "サロン名" : s_name,
                "アクセス" : s_access,
                "カット単価(円~)" : s_price,
            }
            # データフレーム作成
            df6 = pd.DataFrame(data_list)
            # 重複データ処理
            df6.drop_duplicates(inplace=True)
            df6.reset_index(drop=True,inplace=True)
            # SQLでDBにデータ保存
            # SQLiteデータベースへの接続
            db_path = "STEP3チーム課題_TA_IndéMode_DB.db"
            conn = sqlite3.connect(db_path) 
            # データフレームをSQLiteデータベースに書き込む
            table_name = '近隣サロン一覧_楽天beauty'  # テーブル名を適切なものに変更してください
            df6.to_sql(table_name, conn, if_exists='replace', index=False)
            df6['カット単価(円~)'] = df6['カット単価(円~)'].str.replace(',', '').replace('-', '0').astype(float) #データ数値化
            df6 = df6.sort_values(by='カット単価(円~)') #データ整列
            return {
                '緯度': station_latitude,
                '経度': station_longitude,
                '郵便番号': station_postal,
                '利用者数ランク': df1[df1["駅名"] == station][["ランキング"]].values[0],
                '利用者数': df1[df1["駅名"] == station][["利用者数(人/日)"]].values[0],
                'エリア': station_area,
                'エリア賃料相場': area_average_rent,
                'エリア内サロン件数 from 楽天Beauty': len(df6),
                'エリア内カット単価': df6['カット単価(円~)'],   
                'エリア内カット単価平均額': df6['カット単価(円~)'].mean(),   
            }           
        else:
            st.write("該当する駅情報が見つかりませんでした。")
            return None    

    #物件検索関数
    def get_tenanto_info(line, station):
        if station_data:
            # 最初の駅情報を取得
            first_station = station_data[0]
            station_longitude = first_station.get('x')
            station_latitude = first_station.get('y')
            station_postal = first_station.get('postal')
            # 郵便番号検索 APIで緯度経度を元に住所を取得
            postal_url = "https://zipcloud.ibsnet.co.jp/api/search?zipcode=" + station_postal
            postal_response = requests.get(postal_url)
            postal_res = postal_response.json()
            station_area = postal_res['results'][0].get('address2')   
            station_coordinate = (station_latitude, station_longitude)
            # テナントショップから空店舗検索
            # 情報格納のための空配列を用意
            TenantName = [] #name
            TenantPrice = [] # 家賃
            TenantPrice_per_unit_area = [] # 坪単価
            TenantStation = [] # 駅
            #TenantLine = [] # 路線
            #TenantWalk = [] # 駅徒歩
            Tenantlocate = [] # 住所
            Tenantbuild = [] # 築年数
            TenantFloor = [] # 階数
            TenantSize = [] # 平米
            Tenantlongitude = [] # 経度
            Tenantlatitude = [] # 緯度
            Tenantdistance = [] # 指定駅からの距離
            Tenantrisk = [] # 開業リスク
            Tenantinitialinvestiment = [] # 初期投資
            # HTML取得
            area_code_tenant =str(df3[df3["区名"] == station_area].values[0][2])
            URL = 'https://www.tenant-shop.com/index.php?ac=2&c=12&a[]=' + area_code_tenant + '&pa=14&f6=1&sp=3&mv=2&p={}'
            # 緯度経度取得用APIアドレス
            url_1='http://zipcoda.net/api?address='
            url_2 = 'http://geoapi.heartrails.com/api/json?method=searchByPostal&postal='
            # 複数ページ取得のためのループ処理
            for i in range(1,6):
                # 変数trget_urlに、アクセス先のURLを格納する
                load_url = URL.format(i)
                #サーバー負荷低減のための1s待機
                sleep(1)
                # リクエスト
                html = requests.get(load_url)
                # 文字コード変換 (→ utf-8 )
                html.encoding = 'utf-8'
                # BeautifulSoup(解析したいデータ,解析する方法)を指定し、soupに代入
                soup = BeautifulSoup(html.content, "html.parser")
                # sectionデータ(1物件分データ)の取得
                elemsO = soup.find_all("tr",class_="odd result-row")
                elemsE = soup.find_all("tr",class_="even result-row")
                elems = elemsO + elemsE
                # elemsからsectionを1つずつ取り出してelemに代入
                for elem in elems:
                    if (elem.select_one('.pubestno') != None):
                        elem1 = elem.select_one(".pubestno").text #テナント名
                    else:
                        elem1 = "-1"
                    if (elem.select_one('.price') != None):
                        elem2 = elem.select_one('.price').text.replace("万","").replace("～","").replace("(税込)","").replace("(税別)","").replace(" ","").replace("\n","")# 値段をhs2に代入
                    else:
                        elem2 = -1 # 値段が記入されていない場合があるので、わかりやすく-1にしておきましょう。
                    elem3 = elem.select_one('.info')
                    elem40 = elem3.select("div")[1].text
                    #elem40 = re.split('[ |　|\xa0]', elem40)
                    #elem41 = elem40[0]
                    #elem42 = elem40[1]
                    #if (elem40[2] != None):
                    #    elem43 =elem40[2]
                    #else:
                    #      elem43 = -1
                    if len(elem3.select("div")) >= 3:
                        elem5 = elem3.select("div")[2].text
                    else:
                        elem5 = elem3.select("div")[1].text 
                    elem5 = elem3.select("div")[2].text
                    elem6 = elem.select_one(".floor").text.replace("㎡","")
                    elem7 = elem.select(".add")[-1].text
                    elem8 = elem3.select("div")[0].text.replace(" ","")
                    if (elem.select_one('.smallText') != None):
                        elem9 = elem.select_one('.smallText').text.replace("万/坪","").replace("(","").replace(")","")
                    else:
                        elem9 = -1 # 値段が記入されていない場合があるので、わかりやすく-1にしておきましょう。
                    if station_area in elem8:
                        elem8 = elem8
                    else:
                        elem8 = station_area + elem8
                    # ハイフンでテキストを分割
                    split_text = elem8.split("-")
                    if len(split_text) > 1:
                        address = '東京都' + split_text[0]
                    else:
                        address = '東京都' + elem8
                    r = requests.get(url_1 + address)
                    postal=str(r.json()['items'][0]['zipcode'])
                    res_dict = requests.get(url_2+postal).json()['response']['location'][0]
                    elem10 = res_dict['x']
                    elem11 = res_dict['y']
                    tenant_coordinate = (elem11, elem10)
                    elem12 = geodesic(station_coordinate, tenant_coordinate).m
                    # 損益分岐点
                    breakpoint = (60 + int(stylist_count)*int(stylist_salary) + float(elem2))/ 0.75
                    # 想定売上
                    estimated_sale = float(cut_price) * int(seat_count) * float(turnover) * float(operationg_ratio) * 25
                    # 開業リスク
                    elem13 = breakpoint/estimated_sale
                    elem14 = int(interior_cost) * float(elem6)/3.30578
                    # それぞれ抽出したデータを配列に追加
                    TenantPrice.append(elem2) 
                    TenantPrice_per_unit_area.append(elem9) 
                    TenantStation.append(elem40)
                    Tenantbuild.append(elem5)
                    TenantSize.append(float(elem6)/3.30578)
                    TenantFloor.append(elem7)
                    Tenantlocate.append(elem8)  
                    Tenantlongitude.append(elem10)
                    Tenantlatitude.append(elem11)
                    Tenantdistance.append(elem12) 
                    Tenantrisk.append(elem13)
                    Tenantinitialinvestiment.append(elem14)          
            # データ定義
            data_list = {
                "開業リスク" : Tenantrisk,
                "内装費(万円)" : Tenantinitialinvestiment,
                "住所" : Tenantlocate,
                station + "駅からの距離(m)" : Tenantdistance,
                "最寄駅" : TenantStation,
                "賃料(万円)" : TenantPrice,
                "坪単価(万円/坪)" : TenantPrice_per_unit_area,
                "面積(坪)" : TenantSize,    
                "築年" : Tenantbuild,
                "階" : TenantFloor,
                "経度" : Tenantlongitude,
                "緯度" : Tenantlatitude,
            }
            # データフレーム作成
            df8 = pd.DataFrame(data_list)
            # 重複データ処理
            df8.drop_duplicates(inplace=True)
            df8.reset_index(drop=True,inplace=True)
            df8 = df8.round(2)
            df8 = df8.sort_values(by='開業リスク')
            # SQLでDBにデータ保存
            # SQLiteデータベースへの接続
            db_path = "STEP3チーム課題_TA_IndéMode_DB.db"
            conn = sqlite3.connect(db_path) 
            # データフレームをSQLiteデータベースに書き込む
            table_name = '店舗一覧'  # テーブル名を適切なものに変更してください
            df8.to_sql(table_name, conn, if_exists='replace', index=False)
            return {
                '開業リスク': Tenantrisk,
                '内装費≒初期投資(万円)' : Tenantinitialinvestiment,
                'エリア': station_area,
                '住所': Tenantlocate,
                '指定駅からの距離(m)': Tenantdistance,
                '最寄駅': TenantStation,
                '賃料(万円)': TenantPrice,
                '坪単価(万円/坪)': TenantPrice_per_unit_area,
                '面積(坪)': TenantSize,
                '築年': Tenantbuild,
                '階': TenantFloor,
                '空テナント数': len(df8),
                '経度' : Tenantlongitude,
                '緯度' : Tenantlatitude,
            }
        else:
            return None    

    # 関数実行コード
    if response.status_code == 200:
        # エリア調査（get_area_info）関数の呼び出し
        area_info = get_area_info(line, station)
        if area_info is not None:
            # リクエストが成功した場合の処理
            st.write(f'■ ' + station + '駅 の情報')
            st.write(f'   ・首都圏利用者数ランキング:', area_info['利用者数ランク'][0], '位')
            st.write(f'   ・利用者数:',"{:,}".format(int(area_info['利用者数'][0])), '人/日')
            st.write('')
            st.write(f'■ ' + station + '駅所在エリア')
            st.write('   ・エリア:', area_info['エリア'])
            st.write(f'   ・エリア賃料相場:', "{:,}".format(int(area_info['エリア賃料相場'])), '円/坪')
            st.write(f'   ・エリア内サロン件数 from 楽天Beauty:', area_info['エリア内サロン件数 from 楽天Beauty'], '件')
            st.write(f'   ・エリア内カット単価平均額:',  round(area_info['エリア内カット単価平均額']), '円')
            fig, ax = plt.subplots(figsize=(10,6))
            sns.histplot(area_info['エリア内カット単価'], bins=20, kde=True, color='skyblue', ax=ax)  # kde=Trueでカーネル密度推定も表示
            ax.set_xlabel('カット単価(円)')
            ax.set_ylabel('出店件数')
            ax.set_title(f"{area_info['エリア']} サロンのカット単価ヒストグラム")
            st.pyplot(fig)  # Streamlitでのグラフ表示

        # 物件検索（get_tenanto_info）関数の呼び出し
        tenanto_info = get_tenanto_info(line, station)
        if tenanto_info is not None:
            # リクエストが成功した場合の処理
            st.write('■' + area_info['エリア'] + 'の空きテナント検索数:', tenanto_info['空テナント数'], '件')
            # SQLite接続
            conn = sqlite3.connect('STEP3チーム課題_TA_IndéMode_DB.db') 
            # SQLクエリを実行してデータフレームに読み込む
            query8 = 'SELECT * FROM "店舗一覧";'  
            df8 = pd.read_sql_query(query8, conn)
            conn.close()  # データベース接続を閉じる
            df8.drop('緯度', axis=1, inplace=True)
            df8.drop('経度', axis=1, inplace=True)
            st.write(f' ・開業リスクの低いテナント上位5件  ※開業リスク = (目標利益 - 固定費)/(1-変動費率) ÷ 想定売上')
            st.write(df8.head())
            st.write(f'    ※リスク1.0以上の物件は目標利益を見込めない(場合によっては赤字となる)物件です。おススメできませんので開業条件を見直す等ご検討下さい。')
            st.write(f'    ※無料版では目標利益 = 30万円/月、変動費 = 25% で計算しております。詳細に数値設定されたい場合は有料版のご利用をお願い致します。')
            st.write('')

            # おススメ物件を地図に表示
            st.write(f' ・開業リスクの低いテナント上位5件の所在地')
            conn = sqlite3.connect('STEP3チーム課題_TA_IndéMode_DB.db') 
            query8 = 'SELECT * FROM "店舗一覧";'  
            df8 = pd.read_sql_query(query8, conn)
            conn.close()  # データベース接続を閉じる
            df8 = df8.head(5)
            first_station = station_data[0]
            station_longitude = first_station.get('x')
            station_latitude = first_station.get('y')
            map = folium.Map(location=[station_latitude, station_longitude], zoom_start=13)  # 中心座標を設定して地図を作成
            # データフレーム内の各行の緯度と経度をマーカーとして地図上に表示
            for index, row in df8.iterrows():
                folium.Marker([row['緯度'], row['経度']], popup=row['開業リスク']).add_to(map)
                #500mの円を描画
                folium.Circle(
                    location=[row['緯度'], row['経度']],
                    radius= 500,  # 半径をメートルで指定
                    color='#ff0000',  # 円の色
                    fill=True,  # 円を塗りつぶす
                    fill_color='#0000ff',  # 塗りつぶしの色
                    fill_opacity=0.1,  # 塗りつぶしの透明度                        popup='500m圏'  # 円に表示する説明
                ).add_to(map)
            # 地図を表示    
            df8 = df8.rename(columns={'緯度': 'latitude', '経度': 'longitude'})
            df8['latitude'] = df8['latitude'].astype(float)
            df8['longitude'] = df8['longitude'].astype(float)
            st.map(df8) 
            st.write('')

            st.write('■ 開業リスクの低いテナント上位5件の商圏分析')
            # jSTAT MAP認証設定
            REQUEST_URL = 'https://jstatmap.e-stat.go.jp/statmap/api/1.00?category=richReport&func=getSummary'
            USER_ID = '&userid=noriyasukawana@outlook.jp'  #個人の登録ID  
            API_KEY = '&key=dMUbbbyc9ThTzG4PNpA2'  #個人のAPIキー
            # params入力設定
            rangeType = '&rangeType=circle'  # circle(円) or driveTime(到達圏)
            travelMode = '&travelMode=walking'  # car(車) or walking(徒歩)
            speed = '&speed=3.2'  # 時速(km/h)
            time = '&time=15,30,45'  # 移動時間(min)
            output = '&output=json'  # 出力形式
            radius = '&radius=500'
            # 空のdfを用意
            df9 = pd.DataFrame()
            for i in range(5):
                latitude = '&lat=' + str(df8['latitude'][i])  # 緯度 エラー箇所
                longitude = '&lng=' + str(df8['longitude'][i])  # 経度
                res = requests.get(REQUEST_URL + USER_ID + latitude + longitude + rangeType + radius + API_KEY + output)
                result = res.json() 
                #性別別人口
                Gender_pop = result['GET_SUMMARY']['DATASET_INF'][0]['TABLE_INF'][0]['DATA_INF']['VALUE']
                Gender_pop2 = [{key: value for key, value in entry.items() if key not in ['@cat11', '@cat12']} for entry in Gender_pop]
                Gender_pop3 = [entry['$'] for entry in Gender_pop2]
                # リストを3つずつに分割
                list_Gender = [Gender_pop3[i:i+3] for i in range(0, len(Gender_pop3), 3)]
                # DataFrameに変換
                df_Gender = pd.DataFrame(list_Gender, columns=['総人口', '男性人口', '女性人口'])
                #年齢別人口
                Age_pop = result['GET_SUMMARY']['DATASET_INF'][0]['TABLE_INF'][1]['DATA_INF']['VALUE']
                Age_pop2 = [{key: value for key, value in entry.items() if key not in ['@cat11', '@cat13']} for entry in Age_pop]
                Age_pop3 = [entry['$'] for entry in Age_pop2]
                # リストを3つずつに分割
                list_Age = [Age_pop3[i:i+16] for i in range(0, len(Age_pop3), 16)]
                # DataFrameに変換
                df_Age = pd.DataFrame(list_Age, columns=['4 歳以下', '5～9 歳', '10～14 歳', '15～19 歳', '20～24 歳', '25～29 歳', '30～34 歳','35～39 歳', '40～44 歳','45～49 歳', '50～54 歳','55～59 歳', '60～64 歳','65～69 歳', '70～74 歳','75 歳以上'])
                #display(df_Age)
                # DataFrameを結合
                df = pd.concat([df_Gender, df_Age], axis=1)
                # 項目作成
                class_name = result['GET_SUMMARY']['DATASET_INF'][0]['TABLE_INF'][0]['CLASS_INF']['CLASS_OBJ'][0]['CLASS']
                class_name2 = [{key: value for key, value in entry.items() if key not in ['@code']} for entry in class_name]
                class_name3 = [entry['@name'] for entry in class_name2]
                # 項目カラムを用意
                item_column = [str(df8['開業リスク'][i]), class_name3[1], class_name3[2]]
                # 項目カラムをDataFrameの先頭列に追加
                df.insert(0, '開業リスク', item_column)
                df = df.iloc[0]
                # df を df9 に列として追加
                df9 = pd.concat([df9, df], axis=1)
            df9 = df9.T
            df9 = df9.reset_index(drop=True)
            # SQLiteデータベースへの接続
            db_path = "STEP3チーム課題_TA_IndéMode_DB.db"
            conn = sqlite3.connect(db_path) 
            # データフレームをSQLiteデータベースに書き込む
            table_name = '空テナント500m圏内人口構成'  # テーブル名を適切なものに変更してください
            df9.to_sql(table_name, conn, if_exists='replace', index=False)
            # SQLiteデータベース接続

            # df9加工
            df9['20代'] = df9['20～24 歳'].astype(int) + df9['25～29 歳'].astype(int)
            df9['30代'] = df9['30～34 歳'].astype(int) + df9['35～39 歳'].astype(int)
            df9['40代'] = df9['40～44 歳'].astype(int) + df9['45～49 歳'].astype(int)
            df9['50代'] = df9['50～54 歳'].astype(int) + df9['55～59 歳'].astype(int)
            df9['60代'] = df9['60～64 歳'].astype(int) + df9['65～69 歳'].astype(int)
            del df9['4 歳以下']  #列を削除
            del df9['5～9 歳']  
            del df9['10～14 歳'] 
            del df9['20～24 歳'] 
            del df9['25～29 歳'] 
            del df9['30～34 歳'] 
            del df9['35～39 歳'] 
            del df9['40～44 歳'] 
            del df9['45～49 歳'] 
            del df9['50～54 歳'] 
            del df9['55～59 歳']
            del df9['60～64 歳'] 
            del df9['65～69 歳']  
            del df9['75 歳以上']  
            df9['男性比率'] = df9['男性人口'].astype(float) / df9['総人口'].astype(float)
            df9['女性比率'] = df9['女性人口'].astype(float) / df9['総人口'].astype(float)
            del df9['総人口']  
            del df9['男性人口']  
            del df9['女性人口'] 
            df9['15-19歳男性'] =   df9['15～19 歳'].astype(float) * df9['男性比率'].astype(float)
            df9['20代男性'] =   df9['20代'].astype(float) * df9['男性比率'].astype(float)
            df9['30代男性'] =   df9['30代'].astype(float) * df9['男性比率'].astype(float)
            df9['40代男性'] =   df9['40代'].astype(float) * df9['男性比率'].astype(float)
            df9['50代男性'] =   df9['50代'].astype(float) * df9['男性比率'].astype(float)
            df9['60代男性'] =   df9['60代'].astype(float) * df9['男性比率'].astype(float)
            df9['70-74歳男性'] =   df9['70～74 歳'].astype(float) * df9['男性比率'].astype(float)
            df9['15-19歳女性'] =   df9['15～19 歳'].astype(float) * df9['女性比率'].astype(float)
            df9['20代女性'] =   df9['20代'].astype(float) * df9['女性比率'].astype(float)
            df9['30代女性'] =   df9['30代'].astype(float) * df9['女性比率'].astype(float)
            df9['40代女性'] =   df9['40代'].astype(float) * df9['女性比率'].astype(float)
            df9['50代女性'] =   df9['50代'].astype(float) * df9['女性比率'].astype(float)
            df9['60代女性'] =   df9['60代'].astype(float) * df9['女性比率'].astype(float)
            df9['70-74歳女性'] =   df9['70～74 歳'].astype(float) * df9['女性比率'].astype(float)
            del df9['15～19 歳'] 
            del df9['20代'] 
            del df9['30代'] 
            del df9['40代'] 
            del df9['50代'] 
            del df9['60代'] 
            del df9['70～74 歳'] 
            del df9['男性比率'] 
            del df9['女性比率'] 
            # 項目を抜き取る
            df9_item = df9.index
            df10_item = df10['項目']
            del df9['開業リスク']
            del df10['項目']
            # 行同士を掛け合わせる
            result0 = df9.iloc[0] * df10.iloc[2] / 10000000
            result1 = df9.iloc[1] * df10.iloc[2] / 10000000
            result2 = df9.iloc[2] * df10.iloc[2] / 10000000
            result3 = df9.iloc[3] * df10.iloc[2] / 10000000
            result4 = df9.iloc[4] * df10.iloc[2] / 10000000
            # 列方向に結合
            result = pd.concat([pd.DataFrame(result0), pd.DataFrame(result1), pd.DataFrame(result2), pd.DataFrame(result3), pd.DataFrame(result4)], axis=1)
            # 行と列を反転
            result = result.T
            # インデックスリセット
            result = result.set_index(df9_item)
            # 年間総額追加
            result['総額'] = result.sum(axis=1)
            # 指定した列をデータフレームの先頭に移動
            target_column = '総額'
            if target_column in result:
                columns = ['総額'] + [col for col in result if col != '総額']
                result = result[columns]
            st.write('')
            st.write(' ・テナント商圏(500m圏内)居住者の年間サロン利用額(千万円)')
            #display(result)
            # SQLでDBにデータ保存
            # SQLiteデータベースへの接続
            db_path = "STEP3チーム課題_TA_IndéMode_DB.db"
            conn = sqlite3.connect(db_path) 
            # データフレームをSQLiteデータベースに書き込む
            table_name = '商圏サロン利用金額'  # テーブル名を適切なものに変更してください
            result.to_sql(table_name, conn, if_exists='replace', index=False)
            result_male = result[['15-19歳男性', '20代男性', '30代男性', '40代男性', '50代男性', '60代男性','70-74歳男性']]
            result_female = result[['15-19歳女性', '20代女性', '30代女性', '40代女性', '50代女性', '60代女性','70-74歳女性']]
            #棒グラフのX値を指定
            x_male = [0.9, 1.9, 2.9, 3.9, 4.9, 5.9, 6.9]
            x_female = [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1]
            x_label = [1, 2, 3, 4, 5, 6, 7]
            #500m圏内
            for i in range(5):
                fig, ax = plt.subplots() 
                plt.title('(物件' + str(df9_item[i]) + ") 商圏居住者の年間サロン利用額: " + str(int(round(result.loc[df9_item[i],'総額']))) + '千万円', fontsize = 18 )
                plt.xlabel('年齢層', fontsize = 14 )
                plt.ylabel('年間サロン利用額(千万円/年)', fontsize = 14 )
                plt.bar(x_male, result_male.iloc[i] , width = 0.2, label = '男性')
                plt.bar(x_female, result_female.iloc[i] , width = 0.2, label = '女性') 
                plt.grid(axis='y') #y軸グリッド追加
                plt.xticks(x_label, ['15-19歳','20代','30代','40代','50代','60代','70-74歳']) #x軸のx_label位置にラベル記入
                plt.legend()
                plt.ylim(0, 10)  # 0から10までの範囲に調整            
                st.pyplot(fig)
    else:
    # リクエストがエラーの場合の処理
        st.warning("路線名、駅名を再確認して下さい。")































