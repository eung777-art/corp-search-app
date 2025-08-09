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
    body { font-family: 'Roboto', sans-serif; background: #f6f8fa; margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
    .container { margin-top: 60px; background: #fff; padding: 32px 28px 24px 28px; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); min-width: 340px; max-width: 420px; width: 100%; }
    h1 { text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 28px; color: #222; }
    .search-box { display: flex; gap: 8px; margin-bottom: 18px; justify-content: center; }
    input[type=text] { flex: 1; padding: 10px 14px; border: 1px solid #d0d7de; border-radius: 8px; font-size: 1rem; transition: border 0.2s; }
    input[type=text]:focus { border: 1.5px solid #4f8cff; outline: none; }
    input[type=submit] { background: #4f8cff; color: #fff; border: none; border-radius: 8px; padding: 10px 20px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
    input[type=submit]:hover { background: #2563eb; }
    .result { margin-top: 18px; }
    .card-list { list-style: none; padding: 0; margin: 0; }
    .card { background: #f1f5fb; border-radius: 10px; box-shadow: 0 2px 8px rgba(79,140,255,0.06); padding: 18px 16px; margin-bottom: 14px; display: flex; flex-direction: column; transition: box-shadow 0.2s, background 0.2s; }
    .card:hover { background: #e8f0fe; box-shadow: 0 4px 16px rgba(79,140,255,0.13); }
    .corp-name { font-size: 1.1rem; font-weight: 700; color: #222; margin-bottom: 4px; }
    .corp-code { font-size: 0.98rem; color: #4f8cff; font-weight: 500; }
    .view-fin-btn { margin-top: 10px; background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-size: 0.98rem; font-weight: 600; cursor: pointer; transition: background 0.2s; align-self: flex-end; }
    .view-fin-btn:hover { background: #4f8cff; }
    .no-result { text-align: center; color: #888; font-size: 1.05rem; margin-top: 18px; }
    .chart-modal-bg { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.25); align-items: center; justify-content: center; z-index: 1000; }
    .chart-modal { background: #fff; border-radius: 14px; padding: 28px 18px 18px 18px; box-shadow: 0 8px 32px rgba(0,0,0,0.18); min-width: 320px; max-width: 95vw; }
    .modal-close { float: right; font-size: 1.3rem; color: #888; cursor: pointer; margin-top: -10px; margin-right: -6px; }
    .modal-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 12px; color: #222; }
    .ai-btn { margin-top: 12px; background: #ffb74d; color: #222; border: none; border-radius: 6px; padding: 7px 14px; font-size: 0.98rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
    .ai-btn:hover { background: #ffd180; }
    .ai-analysis { margin-top: 16px; background: #f9fbe7; border-radius: 8px; padding: 12px 10px; color: #333; font-size: 1.02rem; min-height: 32px; }
    .balance-sheet-btn { margin-left: 8px; background: #4caf50; color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-size: 0.98rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
    .balance-sheet-btn:hover { background: #45a049; }
    .balance-sheet-modal-bg { display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.25); align-items: center; justify-content: center; z-index: 1000; }
    .balance-sheet-modal { background: #fff; border-radius: 14px; padding: 28px 18px 18px 18px; box-shadow: 0 8px 32px rgba(0,0,0,0.18); min-width: 600px; max-width: 90vw; }
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
              <button class="view-fin-btn" onclick="openFinModal('{{ name }}', '{{ code }}')">재무 시각화</button>
              <button class="balance-sheet-btn" onclick="openBalanceSheetModal('{{ name }}', '{{ code }}')">재무상태표</button>
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
      <canvas id="finChart" width="340" height="260"></canvas>
      <div id="chartMsg" style="margin-top:10px;color:#888;font-size:0.98rem;"></div>
      <button class="ai-btn" id="aiBtn" style="display:none;" onclick="requestAI()">AI 분석 보기</button>
      <div class="ai-analysis" id="aiAnalysis" style="display:none;"></div>
    </div>
  </div>
  <div class="balance-sheet-modal-bg" id="balanceSheetModalBg">
    <div class="balance-sheet-modal">
      <span class="modal-close" onclick="closeBalanceSheetModal()">&times;</span>
      <div class="modal-title" id="balanceSheetModalTitle"></div>
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
      <div id="balanceSheetMsg" style="margin-top:15px;color:#888;font-size:0.98rem;text-align:center;"></div>
    </div>
  </div>
  <script>
    let chart = null;
    let lastTrendData = null;
    let lastCorpName = '';
    function openFinModal(name, code) {
      document.getElementById('modalTitle').innerText = `${name} 주요 계정 연도별 추이 (백만원)`;
      document.getElementById('chartMsg').innerText = '데이터를 불러오는 중...';
      document.getElementById('chartModalBg').style.display = 'flex';
      document.getElementById('aiBtn').style.display = 'none';
      document.getElementById('aiAnalysis').style.display = 'none';
      fetch(`/api/fin_trend?corp_code=${code}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            document.getElementById('chartMsg').innerText = data.message || '데이터를 불러올 수 없습니다.';
            if (chart) { chart.destroy(); chart = null; }
            return;
          }
          lastTrendData = data;
          lastCorpName = name;
          document.getElementById('aiBtn').style.display = 'inline-block';
          const years = data.years;
          const accounts = ['자산총계','부채총계','자본총계','매출액','영업이익','당기순이익'];
          const datasets = accounts.map((acc, idx) => ({
            label: acc,
            data: data.trend[acc],
            borderColor: ['#4f8cff','#ffb74d','#81c784','#e57373','#9575cd','#64b5f6'][idx],
            backgroundColor: 'rgba(0,0,0,0)',
            tension: 0.2,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2
          }));
          if (chart) chart.destroy();
          chart = new Chart(document.getElementById('finChart').getContext('2d'), {
            type: 'line',
            data: { labels: years, datasets },
            options: { responsive: false, plugins: { legend: { display: true } }, scales: { y: { beginAtZero: true, title: { display: true, text: '금액(백만원)' } } } }
          });
          document.getElementById('chartMsg').innerText = '';
        })
        .catch(() => {
          document.getElementById('chartMsg').innerText = '데이터를 불러올 수 없습니다.';
          if (chart) { chart.destroy(); chart = null; }
        });
    }
    function closeFinModal() {
      document.getElementById('chartModalBg').style.display = 'none';
      if (chart) { chart.destroy(); chart = null; }
    }
    function requestAI() {
      document.getElementById('aiAnalysis').style.display = 'block';
      document.getElementById('aiAnalysis').innerText = 'AI가 분석 중입니다...';
      fetch('/api/ai_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: lastCorpName, trend: lastTrendData })
      })
      .then(r => r.json())
      .then(data => {
        document.getElementById('aiAnalysis').innerText = data.analysis || 'AI 분석 결과를 받아올 수 없습니다.';
      })
      .catch(() => {
        document.getElementById('aiAnalysis').innerText = 'AI 분석 결과를 받아올 수 없습니다.';
      });
    }
    function openBalanceSheetModal(name, code) {
      document.getElementById('balanceSheetModalTitle').innerText = `${name} 재무상태표`;
      document.getElementById('balanceSheetMsg').innerText = '데이터를 불러오는 중...';
      document.getElementById('balanceSheetModalBg').style.display = 'flex';
      
      // 초기화
      document.getElementById('assetAmount').innerText = '-';
      document.getElementById('liabilityAmount').innerText = '-';
      document.getElementById('equityAmount').innerText = '-';
      resetBoxHeights();
      
      fetch(`/api/balance_sheet?corp_code=${code}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            document.getElementById('balanceSheetMsg').innerText = data.message || '데이터를 불러올 수 없습니다.';
            return;
          }
          
          const asset = data.asset;
          const liability = data.liability;
          const equity = data.equity;
          
          // 금액 표시
          document.getElementById('assetAmount').innerText = formatAmount(asset);
          document.getElementById('liabilityAmount').innerText = formatAmount(liability);
          document.getElementById('equityAmount').innerText = formatAmount(equity);
          
          // 박스 높이 조절
          adjustBoxHeights(asset, liability, equity);
          
          document.getElementById('balanceSheetMsg').innerText = `자산 = 부채(${formatAmount(liability)}) + 자본(${formatAmount(equity)}) = ${formatAmount(liability + equity)}`;
        })
        .catch(() => {
          document.getElementById('balanceSheetMsg').innerText = '데이터를 불러올 수 없습니다.';
        });
    }
    
    function closeBalanceSheetModal() {
      document.getElementById('balanceSheetModalBg').style.display = 'none';
    }
    
    function formatAmount(amount) {
      if (amount === null || amount === undefined) return '-';
      return `${amount.toLocaleString()}백만원`;
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
                        val = int(item['thstrm_amount'].replace(',','')) // 1000000
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
    import datetime
    now = datetime.datetime.now()
    current_year = str(now.year - 1)  # 작년 데이터
    
    params = {
        'crtfc_key': DART_API_KEY,
        'corp_code': corp_code,
        'bsns_year': current_year,
        'reprt_code': '11011',
    }
    url = 'https://opendart.fss.or.kr/api/fnlttSinglAcnt.json'
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if data.get('status') != '000':
            return jsonify({'success': False, 'message': '재무상태표 데이터를 불러올 수 없습니다.'})
        
        # 재무상태표 계정 찾기
        accounts = data.get('list', [])
        
        def find_account_amount(account_name):
            item = next((x for x in accounts if x['account_nm'] == account_name), None)
            if item and item.get('thstrm_amount'):
                try:
                    return int(item['thstrm_amount'].replace(',','')) // 1000000  # 백만원 단위
                except Exception:
                    return 0
            return 0
        
        asset = find_account_amount('자산총계')
        liability = find_account_amount('부채총계') 
        equity = find_account_amount('자본총계')
        
        # 자산 = 부채 + 자본 검증
        if asset == 0 and liability == 0 and equity == 0:
            return jsonify({'success': False, 'message': '재무상태표 데이터가 없습니다.'})
        
        return jsonify({
            'success': True,
            'year': current_year,
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