from flask import Flask, render_template_string, request, jsonify
import sqlite3
import requests
import os

app = Flask(__name__)
DB_PATH = os.getenv('DB_PATH', 'corp.db')
DART_API_KEY = os.getenv('DART_API_KEY', '11505e64336a7acc9b46e7ae3cd38cbf75f20682')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyATEeK4pwPJ8Np-QqEqaQKGwuAdlgoyDWU')
GEMINI_MODEL = 'gemini-1.5-flash'

HTML = '''
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>회사명으로 corp_code 검색</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: 'Roboto', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
    .container { margin-top: 40px; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); padding: 40px 32px 32px 32px; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); min-width: 380px; max-width: 480px; width: 100%; border: 1px solid rgba(255,255,255,0.2); }
    h1 { text-align: center; font-size: 2.2rem; font-weight: 800; margin-bottom: 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .search-box { display: flex; gap: 12px; margin-bottom: 24px; justify-content: center; }
    input[type=text] { flex: 1; padding: 14px 18px; border: 2px solid rgba(102, 126, 234, 0.2); border-radius: 12px; font-size: 1.1rem; transition: all 0.3s ease; background: rgba(255,255,255,0.8); }
    input[type=text]:focus { border: 2px solid #667eea; outline: none; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15); }
    input[type=submit] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; border-radius: 12px; padding: 14px 24px; font-size: 1.1rem; font-weight: 700; cursor: pointer; transition: all 0.3s ease; }
    input[type=submit]:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3); }
    .result { margin-top: 24px; }
    .card-list { list-style: none; padding: 0; margin: 0; }
    .card { background: rgba(255,255,255,0.9); border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 24px 20px; margin-bottom: 20px; display: flex; flex-direction: column; transition: all 0.3s ease; border: 1px solid rgba(255,255,255,0.3); }
    .card:hover { background: rgba(255,255,255,1); box-shadow: 0 8px 32px rgba(0,0,0,0.12); transform: translateY(-4px); }
    .corp-name { font-size: 1.3rem; font-weight: 800; color: #2d3748; margin-bottom: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .corp-code { font-size: 1rem; color: #718096; font-weight: 500; margin-bottom: 16px; }
    .button-container { margin-top: 16px; display: flex; gap: 12px; justify-content: flex-end; }
    .view-fin-btn, .balance-sheet-btn { border: none; border-radius: 12px; padding: 12px 20px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; min-width: 120px; position: relative; overflow: hidden; }
    .view-fin-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }
    .view-fin-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4); }
    .balance-sheet-btn { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #fff; }
    .balance-sheet-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(79, 172, 254, 0.4); }
    .no-result { text-align: center; color: #888; font-size: 1.05rem; margin-top: 18px; }
    .chart-modal-bg { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); align-items: center; justify-content: center; z-index: 1000; }
    .chart-modal { background: rgba(255,255,255,0.98); border-radius: 20px; padding: 32px 24px 24px 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); min-width: 800px; max-width: 95vw; border: 1px solid rgba(255,255,255,0.3); }
    .modal-close { float: right; font-size: 1.5rem; color: #667eea; cursor: pointer; margin-top: -12px; margin-right: -8px; transition: all 0.2s ease; }
    .modal-close:hover { color: #764ba2; transform: scale(1.1); }
    .modal-title { font-size: 1.4rem; font-weight: 800; margin-bottom: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .chart-tabs { display: flex; background: rgba(255,255,255,0.8); border-radius: 12px; padding: 6px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .chart-tab { flex: 1; padding: 12px 20px; text-align: center; background: transparent; border: none; border-radius: 8px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.3s; color: #718096; }
    .chart-tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); }
    .chart-tab:hover:not(.active) { background: rgba(102, 126, 234, 0.1); color: #667eea; }
    .chart-content { display: none; }
    .chart-content.active { display: block; }
    .chart-container { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 20px; }
    .main-chart { background: rgba(248,250,252,0.8); border-radius: 16px; padding: 20px; }
    .chart-stats { display: flex; flex-direction: column; gap: 12px; }
    .stat-card { background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 12px; padding: 16px; border: 1px solid rgba(102, 126, 234, 0.2); }
    .stat-title { font-size: 0.9rem; color: #718096; font-weight: 600; margin-bottom: 4px; }
    .stat-value { font-size: 1.2rem; font-weight: 800; color: #2d3748; }
    .stat-change { font-size: 0.85rem; margin-top: 4px; font-weight: 600; }
    .positive { color: #38a169; }
    .negative { color: #e53e3e; }
    .ai-btn { margin-top: 20px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); color: #2d3748; border: none; border-radius: 12px; padding: 12px 24px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(255, 154, 158, 0.3); }
    .ai-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 154, 158, 0.4); }
    .ai-modal-bg { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.6); backdrop-filter: blur(12px); align-items: center; justify-content: center; z-index: 2000; }
    .ai-modal { background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,154,158,0.05) 100%); border-radius: 24px; padding: 40px 32px 32px 32px; box-shadow: 0 25px 80px rgba(255, 154, 158, 0.3); min-width: 600px; max-width: 80vw; max-height: 80vh; overflow-y: auto; border: 2px solid rgba(255, 154, 158, 0.2); backdrop-filter: blur(20px); }
    .ai-modal-title { font-size: 1.5rem; font-weight: 800; margin-bottom: 24px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-align: center; }
    .ai-loading { text-align: center; padding: 40px 20px; color: #718096; font-size: 1.1rem; }
    .ai-loading::before { content: '🤖'; font-size: 2rem; display: block; margin-bottom: 16px; animation: bounce 1.5s infinite; }
    @keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-10px); } 60% { transform: translateY(-5px); } }
    .ai-analysis-content { background: rgba(255,255,255,0.8); border-radius: 16px; padding: 24px; color: #2d3748; font-size: 1.1rem; line-height: 1.8; border: 1px solid rgba(255, 154, 158, 0.2); white-space: pre-wrap; }
    .balance-sheet-btn:hover { background: #45a049; }
    .balance-sheet-modal-bg { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); align-items: center; justify-content: center; z-index: 1000; }
    .balance-sheet-modal { background: rgba(255,255,255,0.98); border-radius: 20px; padding: 32px 24px 24px 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); min-width: 700px; max-width: 90vw; border: 1px solid rgba(255,255,255,0.3); }
    .year-selector { margin-bottom: 20px; text-align: center; }
    .year-selector label { font-size: 1rem; font-weight: 600; color: #2d3748; margin-right: 12px; }
    .year-selector select { padding: 8px 16px; border: 2px solid rgba(102, 126, 234, 0.2); border-radius: 8px; font-size: 1rem; background: rgba(255,255,255,0.9); transition: all 0.3s ease; }
    .year-selector select:focus { border-color: #667eea; outline: none; }
    .balance-sheet-container { display: flex; gap: 20px; margin-top: 20px; }
    .balance-side { flex: 1; }
    .balance-side h3 { text-align: center; margin-bottom: 15px; font-size: 1.2rem; }
    .balance-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; padding: 15px; margin-bottom: 10px; position: relative; min-height: 60px; display: flex; flex-direction: column; justify-content: center; transition: all 0.3s ease; }
    .balance-box.asset { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .balance-box.liability { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .balance-box.equity { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333; }
    .balance-amount { font-size: 1.1rem; font-weight: bold; text-align: center; }
    .balance-label { font-size: 0.9rem; text-align: center; margin-bottom: 5px; opacity: 0.9; }
    @media (max-width: 500px) { .container { min-width: unset; max-width: 98vw; padding: 18px 4vw 14px 4vw; } h1 { font-size: 1.3rem; } .chart-modal { min-width: unset; } .balance-sheet-modal { min-width: 95vw; } .balance-sheet-container { flex-direction: column; } }
  </style>
</head>
<body>
  <div class="container">
    <h1>회사명으로 corp_code 검색</h1>
    <form method="get" class="search-box">
      <input type="text" name="q" placeholder="회사명을 입력하세요" value="{{ query|default('') }}" required autofocus>
      <input type="submit" value="검색">
    </form>
    {% if results is not none %}
      <div class="result">
        {% if results %}
          <ul class="card-list">
          {% for name, code in results %}
            <li class="card">
              <span class="corp-name">{{ name }}</span>
              <span class="corp-code">corp_code: {{ code }}</span>
              <div class="button-container">
              <button class="view-fin-btn" onclick="openFinModal('{{ name }}', '{{ code }}')">재무 시각화</button>
                <button class="balance-sheet-btn" onclick="openBalanceSheetModal('{{ name }}', '{{ code }}')">재무상태표</button>
              </div>
            </li>
          {% endfor %}
          </ul>
        {% else %}
          <div class="no-result">검색 결과가 없습니다.</div>
        {% endif %}
      </div>
    {% endif %}
  </div>
  <div class="chart-modal-bg" id="chartModalBg">
    <div class="chart-modal">
      <span class="modal-close" onclick="closeFinModal()">&times;</span>
      <div class="modal-title" id="modalTitle"></div>
      
      <!-- 탭 메뉴 -->
      <div class="chart-tabs">
        <button class="chart-tab active" onclick="switchTab('income')">📊 손익계산서</button>
        <button class="chart-tab" onclick="switchTab('balance')">🏦 재무상태표</button>
      </div>
      
      <!-- 손익계산서 탭 -->
      <div id="incomeContent" class="chart-content active">
        <div class="chart-container">
          <div class="main-chart">
            <canvas id="incomeChart" width="480" height="300"></canvas>
            <div id="incomeChartMsg" style="margin-top:12px;color:#718096;font-size:1rem;text-align:center;"></div>
          </div>
          
          <div class="chart-stats">
            <div class="stat-card">
              <div class="stat-title">최신 매출액</div>
              <div class="stat-value" id="latestRevenue">-</div>
              <div class="stat-change" id="revenueChange">-</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-title">최신 영업이익</div>
              <div class="stat-value" id="latestOperatingProfit">-</div>
              <div class="stat-change" id="operatingProfitChange">-</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-title">최신 당기순이익</div>
              <div class="stat-value" id="latestNetIncome">-</div>
              <div class="stat-change" id="netIncomeChange">-</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-title">영업이익률</div>
              <div class="stat-value" id="operatingMargin">-</div>
              <div class="stat-change" id="marginChange">-</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 재무상태표 탭 -->
      <div id="balanceContent" class="chart-content">
        <div class="chart-container">
          <div class="main-chart">
            <canvas id="balanceChart" width="480" height="300"></canvas>
            <div id="balanceChartMsg" style="margin-top:12px;color:#718096;font-size:1rem;text-align:center;"></div>
          </div>
          
          <div class="chart-stats">
            <div class="stat-card">
              <div class="stat-title">자산총계</div>
              <div class="stat-value" id="totalAssets">-</div>
              <div class="stat-change" id="assetChange">-</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-title">부채총계</div>
              <div class="stat-value" id="totalLiabilities">-</div>
              <div class="stat-change" id="liabilityChange">-</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-title">자본총계</div>
              <div class="stat-value" id="totalEquity">-</div>
              <div class="stat-change" id="equityChange">-</div>
            </div>
            
            <div class="stat-card">
              <div class="stat-title">부채비율</div>
              <div class="stat-value" id="debtRatio">-</div>
              <div class="stat-change" id="debtRatioChange">-</div>
            </div>
          </div>
        </div>
      </div>
      
      <button class="ai-btn" id="aiBtn" style="display:none;" onclick="openAIModal()">🤖 AI 분석 보기</button>
    </div>
  </div>
  <div class="balance-sheet-modal-bg" id="balanceSheetModalBg">
    <div class="balance-sheet-modal">
      <span class="modal-close" onclick="closeBalanceSheetModal()">&times;</span>
      <div class="modal-title" id="balanceSheetModalTitle"></div>
      
      <div class="year-selector">
        <label for="yearSelect">📅 조회연도:</label>
        <select id="yearSelect" onchange="changeBalanceSheetYear()">
          <option value="">연도 선택</option>
        </select>
      </div>
      
      <div class="balance-sheet-container">
        <div class="balance-side">
          <h3>📊 자산 (Assets)</h3>
          <div id="assetBox" class="balance-box asset">
            <div class="balance-label">자산총계</div>
            <div class="balance-amount" id="assetAmount">-</div>
          </div>
        </div>
        <div class="balance-side">
          <h3>📈 부채 + 자본</h3>
          <div id="liabilityBox" class="balance-box liability">
            <div class="balance-label">부채총계</div>
            <div class="balance-amount" id="liabilityAmount">-</div>
          </div>
          <div id="equityBox" class="balance-box equity">
            <div class="balance-label">자본총계</div>
            <div class="balance-amount" id="equityAmount">-</div>
          </div>
        </div>
      </div>
      <div id="balanceSheetMsg" style="margin-top:15px;color:#718096;font-size:1rem;text-align:center;font-weight:500;"></div>
      
      <div id="yearComparisonSection" style="margin-top:20px;display:none;">
        <div style="text-align:center;margin-bottom:15px;">
          <strong style="color:#2d3748;font-size:1.1rem;">📊 연도별 변화율</strong>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
          <div class="stat-card" style="text-align:center;">
            <div class="stat-title">자산총계 변화</div>
            <div class="stat-value" id="assetYearChange">-</div>
          </div>
          <div class="stat-card" style="text-align:center;">
            <div class="stat-title">부채총계 변화</div>
            <div class="stat-value" id="liabilityYearChange">-</div>
          </div>
          <div class="stat-card" style="text-align:center;">
            <div class="stat-title">자본총계 변화</div>
            <div class="stat-value" id="equityYearChange">-</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- AI 분석 전용 모달 -->
  <div class="ai-modal-bg" id="aiModalBg">
    <div class="ai-modal">
      <span class="modal-close" onclick="closeAIModal()" style="color:#ff9a9e;">&times;</span>
      <div class="ai-modal-title" id="aiModalTitle">🤖 AI 재무 분석 리포트</div>
      
      <div id="aiLoadingSection" class="ai-loading">
        AI가 재무 데이터를 분석하고 있습니다...
      </div>
      
      <div id="aiAnalysisSection" style="display:none;">
        <div class="ai-analysis-content" id="aiAnalysisContent"></div>
      </div>
    </div>
  </div>
  
  <script>
    let incomeChart = null;
    let balanceChart = null;
    let lastTrendData = null;
    let lastCorpName = '';
    let currentTab = 'income';
    
    function switchTab(tabName) {
      // 탭 활성화 상태 변경
      document.querySelectorAll('.chart-tab').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.chart-content').forEach(content => content.classList.remove('active'));
      
      event.target.classList.add('active');
      document.getElementById(tabName + 'Content').classList.add('active');
      
      currentTab = tabName;
      
      // 현재 탭에 맞는 차트 생성
      if (lastTrendData) {
        if (tabName === 'income') {
          createIncomeChart(lastTrendData);
        } else if (tabName === 'balance') {
          createBalanceChart(lastTrendData);
        }
      }
    }
    
    function openFinModal(name, code) {
      document.getElementById('modalTitle').innerText = `${name} 재무 데이터 분석 (억원)`;
      document.getElementById('incomeChartMsg').innerText = '데이터를 불러오는 중...';
      document.getElementById('balanceChartMsg').innerText = '데이터를 불러오는 중...';
      document.getElementById('chartModalBg').style.display = 'flex';
      document.getElementById('aiBtn').style.display = 'none';
      
      // 손익계산서 탭을 기본으로 활성화
      switchTab('income');
      fetch(`/api/fin_trend?corp_code=${code}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            document.getElementById('incomeChartMsg').innerText = data.message || '데이터를 불러올 수 없습니다.';
            document.getElementById('balanceChartMsg').innerText = data.message || '데이터를 불러올 수 없습니다.';
            return;
          }
          lastTrendData = data;
          lastCorpName = name;
          document.getElementById('aiBtn').style.display = 'inline-block';
          
          // 현재 활성화된 탭에 맞는 차트 생성
          if (currentTab === 'income') {
            createIncomeChart(data);
          } else {
            createBalanceChart(data);
          }
        })
        .catch(() => {
          document.getElementById('incomeChartMsg').innerText = '데이터를 불러오는 중 오류가 발생했습니다.';
          document.getElementById('balanceChartMsg').innerText = '데이터를 불러오는 중 오류가 발생했습니다.';
        });
    }
    
    function createIncomeChart(data) {
      const years = data.years;
      const incomeAccounts = ['매출액', '영업이익', '당기순이익'];
      
      const datasets = incomeAccounts.map((acc, idx) => {
        const colors = [
          { border: '#667eea', bg: 'rgba(102, 126, 234, 0.1)' },
          { border: '#43e97b', bg: 'rgba(67, 233, 123, 0.1)' },
          { border: '#fa709a', bg: 'rgba(250, 112, 154, 0.1)' }
        ];
        return {
          label: acc,
          data: data.trend[acc] || [],
          borderColor: colors[idx].border,
          backgroundColor: colors[idx].bg,
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: colors[idx].border,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        };
      });
      
      document.getElementById('incomeChartMsg').innerText = '';
      if (incomeChart) incomeChart.destroy();
      const ctx = document.getElementById('incomeChart').getContext('2d');
      incomeChart = new Chart(ctx, {
        type: 'line',
        data: { labels: years, datasets: datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { 
              position: 'top',
              labels: { 
                boxWidth: 12, 
                padding: 15,
                font: { size: 12, weight: '600' },
                color: '#4a5568'
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: '금액(억원)', font: { size: 14 } },
              grid: { color: 'rgba(0,0,0,0.05)' },
              ticks: { font: { size: 12 }, color: '#718096' }
            },
            x: {
              title: { display: true, text: '연도', font: { size: 14 } },
              grid: { color: 'rgba(0,0,0,0.05)' },
              ticks: { font: { size: 12 }, color: '#718096' }
            }
          }
        }
      });
      
      updateIncomeStats(data);
    }
    
    function createBalanceChart(data) {
      const years = data.years;
      const balanceAccounts = ['자산총계', '부채총계', '자본총계'];
      
      const datasets = balanceAccounts.map((acc, idx) => {
        const colors = [
          { border: '#4facfe', bg: 'rgba(79, 172, 254, 0.6)' },
          { border: '#f093fb', bg: 'rgba(240, 147, 251, 0.6)' },
          { border: '#fee140', bg: 'rgba(254, 225, 64, 0.6)' }
        ];
        return {
          label: acc,
          data: data.trend[acc] || [],
          backgroundColor: colors[idx].bg,
          borderColor: colors[idx].border,
          borderWidth: 2
        };
      });
      
      document.getElementById('balanceChartMsg').innerText = '';
      if (balanceChart) balanceChart.destroy();
      const ctx = document.getElementById('balanceChart').getContext('2d');
      balanceChart = new Chart(ctx, {
        type: 'bar',
        data: { labels: years, datasets: datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { 
              position: 'top',
              labels: { 
                boxWidth: 12, 
                padding: 15,
                font: { size: 12, weight: '600' },
                color: '#4a5568'
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: '금액(억원)', font: { size: 14 } },
              grid: { color: 'rgba(0,0,0,0.05)' },
              ticks: { font: { size: 12 }, color: '#718096' }
            },
            x: {
              title: { display: true, text: '연도', font: { size: 14 } },
              grid: { color: 'rgba(0,0,0,0.05)' },
              ticks: { font: { size: 12 }, color: '#718096' }
            }
          }
        }
      });
      
      updateBalanceStats(data);
    }
    function updateIncomeStats(data) {
      const trend = data.trend;
      const years = data.years;
      const latest = years.length - 1;
      const previous = latest - 1;
      
      // 매출액
      const revenue = trend['매출액'];
      if (revenue && revenue.length > latest) {
        document.getElementById('latestRevenue').innerText = revenue[latest] ? `${revenue[latest].toLocaleString()}억원` : '-';
        if (previous >= 0 && revenue[previous]) {
          const change = ((revenue[latest] - revenue[previous]) / revenue[previous] * 100).toFixed(1);
          document.getElementById('revenueChange').innerText = `전년대비 ${change}%`;
          document.getElementById('revenueChange').className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      // 영업이익
      const operatingProfit = trend['영업이익'];
      if (operatingProfit && operatingProfit.length > latest) {
        document.getElementById('latestOperatingProfit').innerText = operatingProfit[latest] ? `${operatingProfit[latest].toLocaleString()}억원` : '-';
        if (previous >= 0 && operatingProfit[previous]) {
          const change = ((operatingProfit[latest] - operatingProfit[previous]) / operatingProfit[previous] * 100).toFixed(1);
          document.getElementById('operatingProfitChange').innerText = `전년대비 ${change}%`;
          document.getElementById('operatingProfitChange').className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      // 당기순이익
      const netIncome = trend['당기순이익'];
      if (netIncome && netIncome.length > latest) {
        document.getElementById('latestNetIncome').innerText = netIncome[latest] ? `${netIncome[latest].toLocaleString()}억원` : '-';
        if (previous >= 0 && netIncome[previous]) {
          const change = ((netIncome[latest] - netIncome[previous]) / netIncome[previous] * 100).toFixed(1);
          document.getElementById('netIncomeChange').innerText = `전년대비 ${change}%`;
          document.getElementById('netIncomeChange').className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      // 영업이익률
      if (revenue && operatingProfit && revenue[latest] && operatingProfit[latest]) {
        const margin = (operatingProfit[latest] / revenue[latest] * 100).toFixed(1);
        document.getElementById('operatingMargin').innerText = `${margin}%`;
        if (previous >= 0 && revenue[previous] && operatingProfit[previous]) {
          const prevMargin = (operatingProfit[previous] / revenue[previous] * 100);
          const marginChange = (margin - prevMargin).toFixed(1);
          document.getElementById('marginChange').innerText = `전년대비 ${marginChange}%p`;
          document.getElementById('marginChange').className = `stat-change ${marginChange >= 0 ? 'positive' : 'negative'}`;
        }
      }
    }
    
    function updateBalanceStats(data) {
      const trend = data.trend;
      const years = data.years;
      const latest = years.length - 1;
      const previous = latest - 1;
      
      // 자산총계
      const assets = trend['자산총계'];
      if (assets && assets.length > latest) {
        document.getElementById('totalAssets').innerText = assets[latest] ? `${assets[latest].toLocaleString()}억원` : '-';
        if (previous >= 0 && assets[previous]) {
          const change = ((assets[latest] - assets[previous]) / assets[previous] * 100).toFixed(1);
          document.getElementById('assetChange').innerText = `전년대비 ${change}%`;
          document.getElementById('assetChange').className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      // 부채총계
      const liabilities = trend['부채총계'];
      if (liabilities && liabilities.length > latest) {
        document.getElementById('totalLiabilities').innerText = liabilities[latest] ? `${liabilities[latest].toLocaleString()}억원` : '-';
        if (previous >= 0 && liabilities[previous]) {
          const change = ((liabilities[latest] - liabilities[previous]) / liabilities[previous] * 100).toFixed(1);
          document.getElementById('liabilityChange').innerText = `전년대비 ${change}%`;
          document.getElementById('liabilityChange').className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      // 자본총계
      const equity = trend['자본총계'];
      if (equity && equity.length > latest) {
        document.getElementById('totalEquity').innerText = equity[latest] ? `${equity[latest].toLocaleString()}억원` : '-';
        if (previous >= 0 && equity[previous]) {
          const change = ((equity[latest] - equity[previous]) / equity[previous] * 100).toFixed(1);
          document.getElementById('equityChange').innerText = `전년대비 ${change}%`;
          document.getElementById('equityChange').className = `stat-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      // 부채비율
      if (assets && liabilities && assets[latest] && liabilities[latest]) {
        const debtRatio = (liabilities[latest] / assets[latest] * 100).toFixed(1);
        document.getElementById('debtRatio').innerText = `${debtRatio}%`;
        if (previous >= 0 && assets[previous] && liabilities[previous]) {
          const prevDebtRatio = (liabilities[previous] / assets[previous] * 100);
          const ratioChange = (debtRatio - prevDebtRatio).toFixed(1);
          document.getElementById('debtRatioChange').innerText = `전년대비 ${ratioChange}%p`;
          document.getElementById('debtRatioChange').className = `stat-change ${ratioChange <= 0 ? 'positive' : 'negative'}`;
        }
      }
    }
    
    function closeFinModal() {
      document.getElementById('chartModalBg').style.display = 'none';
      if (incomeChart) { incomeChart.destroy(); incomeChart = null; }
      if (balanceChart) { balanceChart.destroy(); balanceChart = null; }
    }
    function openAIModal() {
      if (!lastTrendData || !lastCorpName) {
        alert('재무 데이터를 먼저 불러와주세요.');
        return;
      }
      
      // AI 모달 열기
      document.getElementById('aiModalBg').style.display = 'flex';
      document.getElementById('aiModalTitle').innerText = `🤖 ${lastCorpName} AI 재무 분석 리포트`;
      
      // 초기 상태 설정
      document.getElementById('aiLoadingSection').style.display = 'block';
      document.getElementById('aiAnalysisSection').style.display = 'none';
      
      // AI 분석 요청
      fetch('/api/ai_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: lastCorpName, trend: lastTrendData })
      })
      .then(r => r.json())
      .then(data => {
        // 로딩 숨기고 결과 표시
        document.getElementById('aiLoadingSection').style.display = 'none';
        document.getElementById('aiAnalysisSection').style.display = 'block';
        document.getElementById('aiAnalysisContent').innerText = data.analysis || 'AI 분석 결과를 받아올 수 없습니다.';
      })
      .catch(() => {
        document.getElementById('aiLoadingSection').style.display = 'none';
        document.getElementById('aiAnalysisSection').style.display = 'block';
        document.getElementById('aiAnalysisContent').innerText = 'AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
      });
    }
    
    function closeAIModal() {
      document.getElementById('aiModalBg').style.display = 'none';
    }
    let balanceSheetCache = {};
    let currentCorpCode = '';
    
    function openBalanceSheetModal(name, code) {
      currentCorpCode = code;
      document.getElementById('balanceSheetModalTitle').innerText = `${name} 재무상태표`;
      document.getElementById('balanceSheetMsg').innerText = '데이터를 불러오는 중...';
      document.getElementById('balanceSheetModalBg').style.display = 'flex';
      
      // 초기화
      document.getElementById('assetAmount').innerText = '-';
      document.getElementById('liabilityAmount').innerText = '-';
      document.getElementById('equityAmount').innerText = '-';
      resetBoxHeights();
      
      // 연도 선택 드롭다운 초기화
      const yearSelect = document.getElementById('yearSelect');
      yearSelect.innerHTML = '<option value="">데이터 로딩 중...</option>';
      
      // 캐시에서 데이터 확인
      if (balanceSheetCache[code]) {
        populateYearOptions(balanceSheetCache[code]);
        displayBalanceSheet(balanceSheetCache[code]);
        return;
      }
      
      // 새로운 데이터 요청
      fetch(`/api/balance_sheet?corp_code=${code}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            document.getElementById('balanceSheetMsg').innerText = data.message || '데이터를 불러올 수 없습니다.';
            return;
          }
          
          // 캐시 저장
          balanceSheetCache[code] = data;
          
          // 연도 옵션 설정
          populateYearOptions(data);
          
          // 최신 연도 데이터 표시
          displayBalanceSheet(data);
        })
        .catch(() => {
          document.getElementById('balanceSheetMsg').innerText = '데이터를 불러올 수 없습니다.';
        });
    }
    
    function populateYearOptions(data) {
      const yearSelect = document.getElementById('yearSelect');
      yearSelect.innerHTML = '';
      
      if (data.available_years) {
        data.available_years.forEach(year => {
          const option = document.createElement('option');
          option.value = year;
          option.textContent = `${year}년`;
          if (year === data.year) {
            option.selected = true;
          }
          yearSelect.appendChild(option);
        });
      } else {
        const option = document.createElement('option');
        option.value = data.year;
        option.textContent = `${data.year}년`;
        option.selected = true;
        yearSelect.appendChild(option);
      }
    }
    
    function displayBalanceSheet(data, selectedYear = null) {
      const year = selectedYear || data.year;
      let asset, liability, equity;
      
      if (data.all_data && data.all_data[year]) {
        const yearData = data.all_data[year];
        asset = yearData.asset;
        liability = yearData.liability;
        equity = yearData.equity;
      } else {
        asset = data.asset;
        liability = data.liability;
        equity = data.equity;
      }
      
      // 금액 표시
      document.getElementById('assetAmount').innerText = formatAmount(asset);
      document.getElementById('liabilityAmount').innerText = formatAmount(liability);
      document.getElementById('equityAmount').innerText = formatAmount(equity);
      
      // 박스 높이 조절
      adjustBoxHeights(asset, liability, equity);
      
      // 제목 업데이트
      document.getElementById('balanceSheetModalTitle').innerText = 
        document.getElementById('balanceSheetModalTitle').innerText.split(' 재무상태표')[0] + ` 재무상태표 (${year}년)`;
      
      document.getElementById('balanceSheetMsg').innerText = 
        `자산 = 부채(${formatAmount(liability)}) + 자본(${formatAmount(equity)}) = ${formatAmount(liability + equity)}`;
      
      // 연도별 비교 기능
      showYearComparison(data, year);
    }
    
    function showYearComparison(data, currentYear) {
      const comparisonSection = document.getElementById('yearComparisonSection');
      
      if (!data.all_data || Object.keys(data.all_data).length < 2) {
        comparisonSection.style.display = 'none';
        return;
      }
      
      const years = Object.keys(data.all_data).sort();
      const currentIndex = years.indexOf(currentYear);
      
      if (currentIndex === -1 || currentIndex === 0) {
        comparisonSection.style.display = 'none';
        return;
      }
      
      const previousYear = years[currentIndex - 1];
      const currentData = data.all_data[currentYear];
      const previousData = data.all_data[previousYear];
      
      // 변화율 계산
      function calculateChange(current, previous) {
        if (!previous || previous === 0) return null;
        return ((current - previous) / previous * 100).toFixed(1);
      }
      
      const assetChange = calculateChange(currentData.asset, previousData.asset);
      const liabilityChange = calculateChange(currentData.liability, previousData.liability);
      const equityChange = calculateChange(currentData.equity, previousData.equity);
      
      // 변화율 표시
      function displayChange(elementId, change) {
        const element = document.getElementById(elementId);
        if (change === null) {
          element.innerText = '-';
          element.className = 'stat-value';
        } else {
          element.innerText = `${change > 0 ? '+' : ''}${change}%`;
          element.className = `stat-value ${change >= 0 ? 'positive' : 'negative'}`;
        }
      }
      
      displayChange('assetYearChange', assetChange);
      displayChange('liabilityYearChange', liabilityChange);
      displayChange('equityYearChange', equityChange);
      
      comparisonSection.style.display = 'block';
    }
    
    function changeBalanceSheetYear() {
      const selectedYear = document.getElementById('yearSelect').value;
      if (!selectedYear || !currentCorpCode) return;
      
      const cachedData = balanceSheetCache[currentCorpCode];
      if (cachedData && cachedData.all_data && cachedData.all_data[selectedYear]) {
        // 캐시된 데이터 사용
        displayBalanceSheet(cachedData, selectedYear);
      } else {
        // 새로운 연도 데이터 요청
        document.getElementById('balanceSheetMsg').innerText = '데이터를 불러오는 중...';
        fetch(`/api/balance_sheet?corp_code=${currentCorpCode}&year=${selectedYear}`)
          .then(r => r.json())
          .then(data => {
            if (data.success) {
              displayBalanceSheet(data);
            } else {
              document.getElementById('balanceSheetMsg').innerText = data.message || '데이터를 불러올 수 없습니다.';
            }
          })
          .catch(() => {
            document.getElementById('balanceSheetMsg').innerText = '데이터를 불러올 수 없습니다.';
          });
      }
    }
    
    function closeBalanceSheetModal() {
      document.getElementById('balanceSheetModalBg').style.display = 'none';
    }
    
    function formatAmount(amount) {
      if (amount === null || amount === undefined) return '-';
      return `${amount.toLocaleString()}억원`;
    }
    
    function adjustBoxHeights(asset, liability, equity) {
      const maxAmount = Math.max(asset, liability + equity);
      const minHeight = 80;
      const maxHeight = 300;
      
      // 자산 박스 높이
      const assetHeight = minHeight + (asset / maxAmount) * (maxHeight - minHeight);
      document.getElementById('assetBox').style.height = `${assetHeight}px`;
      
      // 부채+자본 총 높이
      const totalRightHeight = minHeight + ((liability + equity) / maxAmount) * (maxHeight - minHeight);
      
      // 부채와 자본의 비율에 따라 높이 분배
      const liabilityRatio = liability / (liability + equity);
      const equityRatio = equity / (liability + equity);
      
      const liabilityHeight = totalRightHeight * liabilityRatio;
      const equityHeight = totalRightHeight * equityRatio;
      
      document.getElementById('liabilityBox').style.height = `${liabilityHeight}px`;
      document.getElementById('equityBox').style.height = `${equityHeight}px`;
    }
    
    function resetBoxHeights() {
      document.getElementById('assetBox').style.height = '80px';
      document.getElementById('liabilityBox').style.height = '80px';
      document.getElementById('equityBox').style.height = '80px';
    }
    
    window.onclick = function(event) {
      if (event.target === document.getElementById('chartModalBg')) closeFinModal();
      if (event.target === document.getElementById('balanceSheetModalBg')) closeBalanceSheetModal();
      if (event.target === document.getElementById('aiModalBg')) closeAIModal();
    }
  </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    results = None
    if query:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT corp_name, corp_code FROM corp WHERE corp_name LIKE ? ORDER BY corp_name LIMIT 20", (f"%{query}%",))
        results = cursor.fetchall()
        conn.close()
    return render_template_string(HTML, query=query, results=results)

@app.route('/api/fin_trend')
def api_fin_trend():
    corp_code = request.args.get('corp_code')
    import datetime
    now = datetime.datetime.now()
    years = [str(now.year - i - 1) for i in range(3)]  # 최근 3년 (작년~3년전)
    accounts = ['자산총계','부채총계','자본총계','매출액','영업이익','당기순이익']
    trend = {acc: [] for acc in accounts}
    for year in years:
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': '11011',
        }
        url = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if data.get('status') != '000':
                for acc in accounts:
                    trend[acc].append(None)
                continue
            # 계정별 금액 추출 (백만원 단위)
            for acc in accounts:
                item = next((x for x in data.get('list', []) if x['account_nm'] == acc), None)
                if item and item.get('thstrm_amount'):
                    try:
                        val = int(item['thstrm_amount'].replace(',','')) // 100000000  # 억원 단위
                    except Exception:
                        val = None
                else:
                    val = None
                trend[acc].append(val)
        except Exception:
            for acc in accounts:
                trend[acc].append(None)
    return jsonify({'success': True, 'years': years[::-1], 'trend': {k: v[::-1] for k,v in trend.items()}})

@app.route('/api/balance_sheet')
def api_balance_sheet():
    corp_code = request.args.get('corp_code')
    year = request.args.get('year')
    
    import datetime
    now = datetime.datetime.now()
    
    # 연도가 지정되지 않으면 기본적으로 최근 5년 데이터를 모두 반환
    if not year:
        years = [str(now.year - i - 1) for i in range(5)]  # 최근 5년
        all_data = {}
        available_years = []
        
        for y in years:
            params = {
                'crtfc_key': DART_API_KEY,
                'corp_code': corp_code,
                'bsns_year': y,
                'reprt_code': '11011',
            }
            url = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
            
            try:
                r = requests.get(url, params=params, timeout=10)
                data = r.json()
                
                if data.get('status') == '000':
                    accounts = data.get('list', [])
                    
                    def find_account_amount(account_name):
                        item = next((x for x in accounts if x['account_nm'] == account_name), None)
                        if item and item.get('thstrm_amount'):
                            try:
                                return int(item['thstrm_amount'].replace(',','')) // 100000000  # 억원 단위
                            except Exception:
                                return 0
                        return 0
                    
                    asset = find_account_amount('자산총계')
                    liability = find_account_amount('부채총계') 
                    equity = find_account_amount('자본총계')
                    
                    if asset > 0 or liability > 0 or equity > 0:
                        all_data[y] = {
                            'asset': asset,
                            'liability': liability,
                            'equity': equity
                        }
                        available_years.append(y)
                        
            except Exception:
                continue
        
        if not available_years:
            return jsonify({'success': False, 'message': '재무상태표 데이터가 없습니다.'})
        
        # 최신 연도 데이터를 기본으로 반환
        latest_year = max(available_years)
        latest_data = all_data[latest_year]
        
        return jsonify({
            'success': True,
            'year': latest_year,
            'asset': latest_data['asset'],
            'liability': latest_data['liability'],
            'equity': latest_data['equity'],
            'available_years': sorted(available_years, reverse=True),
            'all_data': all_data
        })
    
    # 특정 연도 데이터 요청
    else:
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': '11011',
        }
        url = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
        
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            
            if data.get('status') != '000':
                return jsonify({'success': False, 'message': f'{year}년 재무상태표 데이터를 불러올 수 없습니다.'})
            
            accounts = data.get('list', [])
            
            def find_account_amount(account_name):
                item = next((x for x in accounts if x['account_nm'] == account_name), None)
                if item and item.get('thstrm_amount'):
                    try:
                        return int(item['thstrm_amount'].replace(',','')) // 100000000  # 억원 단위
                    except Exception:
                        return 0
                return 0
            
            asset = find_account_amount('자산총계')
            liability = find_account_amount('부채총계') 
            equity = find_account_amount('자본총계')
            
            if asset == 0 and liability == 0 and equity == 0:
                return jsonify({'success': False, 'message': f'{year}년 재무상태표 데이터가 없습니다.'})
            
            return jsonify({
                'success': True,
                'year': year,
                'asset': asset,
                'liability': liability,
                'equity': equity
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'API 오류: {str(e)}'})

@app.route('/api/ai_analysis', methods=['POST'])
def api_ai_analysis():
    import json
    data = request.get_json()
    name = data.get('name')
    trend = data.get('trend')
    years = trend.get('years', [])
    trend_data = trend.get('trend', {})
    prompt = f"""
아래는 {name}의 최근 3년 주요 재무 계정(자산총계, 부채총계, 자본총계, 매출액, 영업이익, 당기순이익) 연도별 추이(단위: 백만원)입니다. 
누구나 이해할 수 있도록 쉽고 친절하게, 숫자와 추세를 요약해 설명해 주세요. 

연도: {', '.join(years)}
"""
    for acc, vals in trend_data.items():
        prompt += f"\n{acc}: {', '.join(str(v) if v is not None else '-' for v in vals)}"
    prompt += "\n\n분석: "
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    def call_gemini():
        r = requests.post(gemini_url, headers=headers, json=payload, timeout=40)
        r.raise_for_status()
        return r.json()
    try:
        try:
            resp = call_gemini()
        except requests.exceptions.Timeout:
            # 1회 재시도
            resp = call_gemini()
        print('Gemini API response:', json.dumps(resp, ensure_ascii=False, indent=2))
        analysis = None
        if 'candidates' in resp and resp['candidates']:
            cand = resp['candidates'][0]
            if 'content' in cand and 'parts' in cand['content'] and cand['content']['parts']:
                part = cand['content']['parts'][0]
                if isinstance(part, dict) and 'text' in part:
                    analysis = part['text']
                elif isinstance(part, str):
                    analysis = part
            elif 'content' in cand and isinstance(cand['content'], str):
                analysis = cand['content']
        if not analysis:
            analysis = f"AI 분석 결과를 받아올 수 없습니다. (응답 구조: {json.dumps(resp, ensure_ascii=False)})"
    except Exception as e:
        print('Gemini API error:', e)
        analysis = f"AI 분석 결과를 받아올 수 없습니다. (에러: {e})"
    return jsonify({'analysis': analysis})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)