import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib
import plotly.express as px

plt.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False
st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")
st.title("📦 Olist E-Commerce Dashboard")


# 데이터 불러오기
@st.cache_data
def load_data():
    orders = pd.read_csv('./data/olist_orders_dataset.csv', parse_dates=['order_purchase_timestamp', 'order_delivered_customer_date'])
    order_items = pd.read_csv('./data/olist_order_items_dataset.csv')
    customers = pd.read_csv('./data/olist_customers_dataset.csv')
    products = pd.read_csv('./data/olist_products_dataset.csv')
    reviews = pd.read_csv('./data/olist_order_reviews_dataset.csv', parse_dates=['review_creation_date'])
    return orders, order_items, customers, products, reviews

orders, order_items, customers, products, reviews = load_data()

orders['year'] = orders['order_purchase_timestamp'].dt.year
orders['month'] = orders['order_purchase_timestamp'].dt.to_period('M')
orders['weekday'] = orders['order_purchase_timestamp'].dt.day_name()
orders['hour'] = orders['order_purchase_timestamp'].dt.hour

# ------------------------
# 주문 분석 탭
# ------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 주문 분석", "🛍️ 상품 분석", "⭐ 리뷰 분석", "🌍 지역 분석", "👥 고객 분석"])

with tab1:
    st.header("📦 주문 분석")

    # 연도 선택
    selected_year = st.selectbox("연도를 선택하세요:", sorted(orders['year'].dropna().unique()))
    year_filtered = orders[orders['year'] == selected_year]

    # 1. 월별 주문 수 (선 그래프)
    monthly = year_filtered['month'].value_counts().sort_index()
    fig1 = px.line(x=monthly.index.astype(str), y=monthly.values,
                   labels={'x': '월', 'y': '주문 수'}, title=f"📈 {selected_year}년 월별 주문 수 추이")
    st.plotly_chart(fig1)

    # 2. 요일별 주문 비율 (파이 차트)
    weekday = year_filtered['weekday'].value_counts()
    fig2 = px.pie(names=weekday.index, values=weekday.values, title=f"🗓️ {selected_year}년 요일별 주문 비율")
    st.plotly_chart(fig2)

    # 3. 주문 상태 분포 (도넛 차트)
    status = year_filtered['order_status'].value_counts()
    fig3 = px.pie(names=status.index, values=status.values,
                  title=f"📦 {selected_year}년 주문 상태 분포", hole=0.4)
    st.plotly_chart(fig3)

    # 4. 시간대별 주문 수 (막대 그래프)
    hourly = year_filtered['hour'].value_counts().sort_index()
    fig4 = px.bar(x=hourly.index, y=hourly.values,
                  labels={'x': '시간대', 'y': '주문 수'}, title=f"⏰ {selected_year}년 시간대별 주문 수")
    st.plotly_chart(fig4)

# 🛍️ 상품 분석
with tab2:
    st.subheader("🛍️ 상품 분석")

    # 데이터 병합
    merged = pd.merge(order_items, orders[['order_id', 'order_purchase_timestamp']], on='order_id')
    merged = pd.merge(merged, products[['product_id', 'product_category_name']], on='product_id')

    col1, col2 = st.columns(2)

    with col1:
        # 카테고리별 판매량 TOP 10
        top_sold = merged['product_category_name'].value_counts().nlargest(10)
        fig1 = px.bar(x=top_sold.index, y=top_sold.values,
                      labels={'x': '상품 카테고리', 'y': '판매 건수'},
                      title='카테고리별 판매량 TOP 10')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # 카테고리별 매주 TOP 10
        sales_by_category = merged.groupby('product_category_name')['price'].sum().sort_values(ascending=False).head(10)
        fig2 = px.bar(x=sales_by_category.index, y=sales_by_category.values,
                      labels={'x': '상품 카테고리', 'y': '총 매주'},
                      title='카테고리별 매주 TOP 10')
        st.plotly_chart(fig2, use_container_width=True)

    # 평균 가격과 판매량 관계 시각화
    grouped = merged.groupby('product_category_name').agg({'price': 'mean', 'order_item_id': 'count'}).reset_index()
    fig3 = px.scatter(grouped, x='price', y='order_item_id',
                      size='order_item_id', hover_name='product_category_name',
                      labels={'price': '평균 가격', 'order_item_id': '판매량'},
                      title='평균 가격과 판매량 관계')
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("⭐ 리뷰 분석")

    # 병합해서 리뷰 작성 소요 시간 구하기
    review_merged = pd.merge(
        reviews[['order_id', 'review_score', 'review_creation_date']],
        orders[['order_id', 'order_purchase_timestamp']],
        on='order_id',
        how='inner'
    )
    review_merged['review_delay'] = (
        review_merged['review_creation_date'] - review_merged['order_purchase_timestamp']
    ).dt.days

    # 점수 분포
    score_counts = review_merged['review_score'].value_counts().sort_index()

    # 평균 점수
    avg_score = review_merged['review_score'].mean()

    # 낮은 점수 비율
    low_rating_ratio = (review_merged['review_score'] <= 2).mean() * 100

    st.markdown("### 리뷰 점수 분포")
    fig1, ax1 = plt.subplots()
    score_counts.plot(kind='bar', ax=ax1)
    ax1.set_xlabel("리뷰 점수")
    ax1.set_ylabel("건수")
    st.pyplot(fig1)

    st.markdown("### 📌 리뷰 통계 요약")
    col1, col2, col3 = st.columns(3)
    col1.metric("🏆 평균 리뷰 점수", f"{avg_score:.2f}")
    col2.metric("📉 낮은 점수 비율 (1~2점)", f"{low_rating_ratio:.1f}%")
    col3.metric("⏱️ 평균 리뷰 작성 지연", f"{review_merged['review_delay'].mean():.1f}일")

with tab4:
    st.subheader("🌍 지역 분석")

    # 주문 + 고객 → 지역 정보 확인
    order_customer = pd.merge(
        orders[['order_id', 'customer_id']],
        customers[['customer_id', 'customer_state']],
        on='customer_id',
        how='left'
    )

    # 주문 + 가격 → 매출 확인
    order_with_price = pd.merge(
        order_customer,
        order_items[['order_id', 'price']],
        on='order_id',
        how='left'
    )

    # 주별 매출 집계
    state_sales = order_with_price.groupby('customer_state')['price'].sum().sort_values(ascending=False)

    # 주별 주문 수 집계
    state_orders = order_with_price.groupby('customer_state')['order_id'].nunique().sort_values(ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 주별 매출 TOP 10")
        fig1, ax1 = plt.subplots()
        state_sales.head(10).plot(kind='bar', ax=ax1)
        ax1.set_ylabel("총 매출")
        ax1.set_xlabel("주")
        st.pyplot(fig1)

    with col2:
        st.markdown("### 주별 주문 수 TOP 10")
        fig2, ax2 = plt.subplots()
        state_orders.head(10).plot(kind='bar', ax=ax2)
        ax2.set_ylabel("주문 건수")
        ax2.set_xlabel("주")
        st.pyplot(fig2)

with tab5:
    st.subheader("👥 고객 분석")

    # 고객별 주문 수
    customer_orders = orders.groupby('customer_id')['order_id'].nunique()
    total_customers = customer_orders.count()
    avg_orders = customer_orders.mean()
    one_time_ratio = (customer_orders == 1).mean() * 100

    # 고객별 총 구매 금액
    order_customer = orders[['order_id', 'customer_id']]
    order_price = pd.merge(order_customer, order_items[['order_id', 'price']], on='order_id')
    customer_sales = order_price.groupby('customer_id')['price'].sum().sort_values(ascending=False)

    # 고객 지역 분포
    customer_state_counts = customers['customer_state'].value_counts().head(10)

    st.markdown("### 📌 고객 통계 요약")
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 전체 고객 수", f"{total_customers:,}")
    col2.metric("🛒 고객당 평균 주문 수", f"{avg_orders:.2f}")
    col3.metric("❌ 한 번만 주문한 고객 비율", f"{one_time_ratio:.1f}%")

    # 고객별 총 구매 금액 TOP 10
    st.markdown("### VIP 고객 (총 구매 금액 기준 Top 10)")
    top_customers = customer_sales.head(10)
    fig1, ax1 = plt.subplots()
    top_customers.plot(kind='bar', ax=ax1)
    ax1.set_ylabel("총 구매 금액")
    ax1.set_xlabel("고객 ID")
    st.pyplot(fig1)

    # 고객 분포
    st.markdown("### 고객 분포 (주별 Top 10)")
    fig2, ax2 = plt.subplots()
    customer_state_counts.plot(kind='bar', ax=ax2)
    ax2.set_ylabel("고객 수")
    ax2.set_xlabel("주")
    st.pyplot(fig2)