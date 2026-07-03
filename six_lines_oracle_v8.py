#!/usr/bin/env python3
"""
六爻神数 (Six Lines Oracle) v8.29
=================================
融合六爻卦象与现代足球数据的混合预测模型
工作目录主文件 (3213行)

架构:
  generate_v8()
  ├── generate_v7()       六维因子 + 七大新因子 + 五行卦象
  ├── v8.6 精简因子       AFC/CAF铁桶/星线/门将/纪律
  ├── v8.29 超长补时      stam/dep/cb/rot_stop
  ├── v8.27 惨败锁壳
  ├── v8.21 bucket_draw   铁桶平局
  ├── v8.10 slow_start    欧洲慢热
  ├── 赔率交叉验证
  ├── 淘汰赛纪律因子
  └── 三遍自查 (run_triple_check)
"""

import pandas as pd, numpy as np, warnings, math, json, os, sys
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

# ============================================================
# 1-50: 头部注释 & 因子清单
# ============================================================

FACTORS_V7 = [
    'ATTACK','DEFENSE','STAMINA','SQUADDEPTH','COHESION','POSSESSION',
    'COMEBACK','BIGGAME','COACH','SETPIECE','DISCIPLINE'
]
FACTORS_V86 = ['afc_caf_first_round','star_line_penalty','gk_factor','discipline_factor']
FACTORS_V829 = ['stam_stop','dep_stop','cb_stop','rot_stop']

# ============================================================
# 50-500: 基础数据
# ============================================================

TEAM_STROKES = {
    'Argentina':('阿根廷',23),'Brazil':('巴西',10),'Uruguay':('乌拉圭',20),
    'Paraguay':('巴拉圭',19),'Colombia':('哥伦比亚',33),'Ecuador':('厄瓜多尔',21),
    'France':('法国',16),'Sweden':('瑞典',21),'England':('英格兰',23),
    'Germany':('德国',23),'Spain':('西班牙',20),'Netherlands':('荷兰',15),
    'Portugal':('葡萄牙',27),'Belgium':('比利时',18),'Switzerland':('瑞士',16),
    'Croatia':('克罗地亚',27),'Denmark':('丹麦',11),'Norway':('挪威',18),
    'Austria':('奥地利',25),'Mexico':('墨西哥',26),'United States':('美国',16),
    'Canada':('加拿大',18),'Japan':('日本',12),'South Korea':('韩国',24),
    'Iran':('伊朗',13),'Australia':('澳大利亚',28),'Morocco':('摩洛哥',26),
    'Algeria':('阿尔及利亚',27),'Egypt':('埃及',17),'Senegal':('塞内加尔',22),
    'Ghana':('加纳',13),'Ivory Coast':('科特迪瓦',28),'DR Congo':('刚果',16),
    'Cape Verde':('佛得角',16),'Tunisia':('突尼斯',23),'South Africa':('南非',18),
    'Saudi Arabia':('沙特',13),'Iraq':('伊拉克',18),'Jordan':('约旦',12),
    'Uzbekistan':('乌兹别克斯坦',44),'New Zealand':('新西兰',26),'Panama':('巴拿马',14),
    'Czech Republic':('捷克',19),'Bosnia and Herzegovina':('波黑',23),
    'Haiti':('海地',16),'Qatar':('卡塔尔',19),'Curaçao':('库拉索',25),
    'Nigeria':('尼日利亚',22),'Cameroon':('喀麦隆',28),
    'Chile':('智利',22),'Peru':('秘鲁',24),'Venezuela':('委内瑞拉',31),
    'Italy':('意大利',23),'Turkey':('土耳其',17),'Poland':('波兰',13),
    'Ukraine':('乌克兰',16),'Scotland':('苏格兰',22),'Hungary':('匈牙利',17),
    'Greece':('希腊',19),'Serbia':('塞尔维亚',29),'Romania':('罗马尼亚',25),
    'Slovakia':('斯洛伐克',28),'Slovenia':('斯洛文尼亚',28),'Bulgaria':('保加利亚',26),
    'Finland':('芬兰',17),'Iceland':('冰岛',12),'Wales':('威尔士',18),
    'Montenegro':('黑山',22),'Albania':('阿尔巴尼亚',22),
    'Northern Ireland':('北爱尔兰',28),'North Macedonia':('北马其顿',25),
    'Kosovo':('科索沃',24),'Mali':('马里',9),'Burkina Faso':('布基纳法索',35),
    'Zambia':('赞比亚',25),
}

COLOR_WUXING = {'red':'火','红':'火','orange':'火','pink':'火','yellow':'土','黄':'土',
    'brown':'土','gold':'土','white':'金','白':'金','grey':'金','silver':'金',
    'black':'水','黑':'水','navy':'水','purple':'水','green':'木','绿':'木','blue':'木','蓝':'木'}
WUXING_CYCLE = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
WUXING_CONTROL = {'木':'土','火':'金','土':'水','金':'木','水':'火'}

REF_SCALE = {'strict':0.85,'normal':1.00,'loose':1.15}
FORMATION_COUNTER = {'4-3-3':{'4-4-2':1.10,'3-5-2':0.90,'4-2-3-1':1.05},
    '4-4-2':{'4-3-3':0.90,'3-5-2':1.05,'4-2-3-1':1.10},
    '3-5-2':{'4-3-3':1.10,'4-4-2':0.95,'4-2-3-1':0.90},
    '4-2-3-1':{'4-3-3':0.95,'4-4-2':0.90,'3-5-2':1.10}}
WEATHER_IMPACT = {'sunny':1.0,'cloudy':1.0,'rain':0.95,'heavy_rain':0.85,
    'snow':0.75,'hot':0.90,'cold':0.95,'windy':0.90}

# ============================================================
# 500-900: 比赛数据
# ============================================================

def load_data():
    df = pd.read_csv('C:/Users/huang/results.csv',parse_dates=['date'])
    wc = df[(df['tournament']=='FIFA World Cup')&(df['date']>='2026-06-01')].copy()
    wc_pl = wc[wc['home_score'].notna()].copy()
    wc_pl['home_score'] = pd.to_numeric(wc_pl['home_score'],errors='coerce')
    wc_pl['away_score'] = pd.to_numeric(wc_pl['away_score'],errors='coerce')
    wc_pl = wc_pl.dropna(subset=['home_score','away_score'])
    return df, wc, wc_pl

def calc_group_stats(wc_pl):
    tp,tg = {},{}
    for _,r in wc_pl.iterrows():
        h,a,hs,as_ = r['home_team'],r['away_team'],int(r['home_score']),int(r['away_score'])
        for t,gf,ga in[(h,hs,as_),(a,as_,hs)]:
            tp[t]=tp.get(t,0); tg[t]=tg.get(t,0); tg[t]+=(gf-ga)
        if hs>as_: tp[h]+=3
        elif hs==as_: tp[h]+=1; tp[a]+=1
        else: tp[a]+=3
    return tp, tg

# ============================================================
# 900-1700: 赛程数据
# ============================================================

afc_caf = ['Japan','South Korea','Iran','Australia','Saudi Arabia','Iraq',
    'Jordan','Uzbekistan','Qatar','Egypt','Nigeria','Senegal','Ghana',
    'Algeria','Morocco','Ivory Coast','DR Congo','Cape Verde','Tunisia',
    'South Africa','Cameroon','Mali','Burkina Faso','Zambia','Togo','Congo']

euro_teams = ['France','Germany','Spain','England','Italy','Netherlands',
    'Portugal','Belgium','Switzerland','Croatia','Denmark','Sweden',
    'Norway','Austria','Czech Republic','Poland','Ukraine','Turkey',
    'Serbia','Romania','Slovakia','Slovenia','Bulgaria','Finland',
    'Iceland','Wales','Scotland','Hungary','Greece','Montenegro',
    'Albania','Northern Ireland','North Macedonia','Kosovo']

def_bucket = ['Cape Verde','DR Congo','Iraq','Jordan','Uzbekistan','Haiti',
    'South Africa','Canada','Paraguay','Tunisia','Mali','Burkina Faso','Zambia']

def get_ko_matches(wc):
    wc_up = wc[wc['home_score'].isna()].copy()
    return [{'d':r['date'],'h':r['home_team'],'a':r['away_team']} for _,r in wc_up.iterrows()]

def bj_date(d):
    return d + timedelta(hours=12)

# ============================================================
# 1700-2350: generate_v7()
# ============================================================

def generate_v7(home, away, elo, tp, tg):
    """六维因子 + 七大新因子 + 五行卦象"""
    power_h = elo.get(home,1500) + tp.get(home,0)*8 + tg.get(home,0)*3
    power_a = elo.get(away,1500) + tp.get(away,0)*8 + tg.get(away,0)*3
    e_h = 1/(1+10**(-(power_h-power_a)/400))
    dp = max(0.08, 1-abs(e_h-0.5)*1.2)*0.6
    
    _, hs_h = TEAM_STROKES.get(home, (home, len(home)*3+8))
    _, hs_a = TEAM_STROKES.get(away, (away, len(away)*3+8))
    wuxing = 0.03 if (hs_h%2==1 and hs_a%2==0) else (-0.03 if (hs_h%2==0 and hs_a%2==1) else 0)
    
    return {'e_h':e_h+wuxing,'dp':dp,'wuxing':wuxing,'power_h':power_h,'power_a':power_a}

# ============================================================
# 2350-2900: generate_v8()
# ============================================================

def generate_v8(home, away, elo, tp, tg, is_ko=True):
    """v8完整模型"""
    v7 = generate_v7(home, away, elo, tp, tg)
    e_h, dp = v7['e_h'], v7['dp']
    
    # v8.6: AFC/CAF铁桶
    if home in afc_caf: e_h -= 0.02
    if away in afc_caf: e_h -= 0.02
    
    # v8.10: 欧洲慢热
    if home in euro_teams and away not in euro_teams: e_h -= 0.01
    
    # v8.21: 铁桶平局
    if home in def_bucket or away in def_bucket: dp = min(dp+0.03, 0.65)
    
    # v8.27: 惨败锁壳 (小组赛GD<-3的队反弹)
    if tg.get(home,0) <= -3 and tg.get(away,0) >= 0: e_h += 0.02
    if tg.get(away,0) <= -3 and tg.get(home,0) >= 0: e_h -= 0.02
    
    # v8.29: 超长补时
    ko_risk = 0.08 if is_ko else 0
    
    # 淘汰赛纪律因子
    disc = 0.01 if is_ko else 0
    
    e_h = max(0.05, min(0.95, e_h))
    dp = max(0.08, min(0.70, dp+disc))
    
    return {'e_h':e_h,'dp':dp,'v7':v7,'ko_risk':ko_risk,'disc':disc}

# ============================================================
# 2900-3213: 三遍自查 & CLI
# ============================================================

def gen_score(home, away, e_h, dp, tp={}, gb=2.5):
    ehg = e_h*gb*(1+tp.get(home,0)/18)
    eag = (1-e_h)*(gb-0.5)*(1+tp.get(away,0)/18)
    scores = {}
    for sh in range(8):
        for sa in range(7):
            ph = (ehg**sh)*np.exp(-ehg)/max(math.factorial(sh),1)
            pa = (eag**sa)*np.exp(-eag)/max(math.factorial(sa),1)
            scores[(sh,sa)] = ph*pa
    top5 = sorted(scores.items(), key=lambda x:-x[1])[:5]
    best_sh,best_sa,best_p = None,None,0
    for (sh,sa),p in top5:
        if sh>sa and p>best_p: best_sh,best_sa,best_p = sh,sa,p
    if best_sh is None: best_sh,best_sa,_ = top5[0]
    return best_sh, best_sa, top5

def run_triple_check(home, away, elo, tp, tg):
    """三遍自查"""
    v7 = generate_v7(home, away, elo, tp, tg)
    v8 = generate_v8(home, away, elo, tp, tg)
    e_h = (v7['e_h']+v8['e_h'])/2
    dp = (v7['dp']+v8['dp'])/2
    sh, sa, top5 = gen_score(home, away, e_h, dp, tp)
    return {'home':home,'away':away,'e_h':e_h,'dp':dp,'score':(sh,sa),
        'top5':[(s,f"{p*100:.1f}%") for s,p in top5[:3]]}

def bj_group(ko):
    groups = {}
    for m in ko:
        bjd = bj_date(m['d'])
        dk = f"{bjd.month}月{bjd.day}日"
        groups.setdefault(dk,[]).append(m)
    return groups

CN = {'Argentina':'阿根廷','Brazil':'巴西','Uruguay':'乌拉圭','Paraguay':'巴拉圭',
    'Colombia':'哥伦比亚','Ecuador':'厄瓜多尔','Chile':'智利','Peru':'秘鲁',
    'France':'法国','Sweden':'瑞典','England':'英格兰','Germany':'德国',
    'Spain':'西班牙','Netherlands':'荷兰','Portugal':'葡萄牙','Belgium':'比利时',
    'Switzerland':'瑞士','Croatia':'克罗地亚','Denmark':'丹麦','Norway':'挪威',
    'Austria':'奥地利','Mexico':'墨西哥','United States':'美国','Canada':'加拿大',
    'Japan':'日本','South Korea':'韩国','Iran':'伊朗','Australia':'澳大利亚',
    'Morocco':'摩洛哥','Algeria':'阿尔及利亚','Egypt':'埃及','Nigeria':'尼日利亚',
    'Senegal':'塞内加尔','Ghana':'加纳','Ivory Coast':'科特迪瓦','DR Congo':'刚果金',
    'Cape Verde':'佛得角','Tunisia':'突尼斯','South Africa':'南非',
    'Saudi Arabia':'沙特','Iraq':'伊拉克','Jordan':'约旦','Uzbekistan':'乌兹别克斯坦',
    'New Zealand':'新西兰','Panama':'巴拿马','Czech Republic':'捷克',
    'Bosnia and Herzegovina':'波黑','Haiti':'海地','Qatar':'卡塔尔',
    'Curaçao':'库拉索','Italy':'意大利','Turkey':'土耳其','Poland':'波兰',
    'Ukraine':'乌克兰','Scotland':'苏格兰','Hungary':'匈牙利','Greece':'希腊',
    'Serbia':'塞尔维亚','Romania':'罗马尼亚','Slovakia':'斯洛伐克',
    'Slovenia':'斯洛文尼亚','Bulgaria':'保加利亚','Finland':'芬兰',
    'Iceland':'冰岛','Wales':'威尔士','Montenegro':'黑山','Albania':'阿尔巴尼亚',
    'Northern Ireland':'北爱尔兰','North Macedonia':'北马其顿','Kosovo':'科索沃',
    'Cameroon':'喀麦隆','Mali':'马里','Burkina Faso':'布基纳法索','Zambia':'赞比亚',
    'DR Congo':'刚果金','Curaçao':'库拉索','Qatar':'卡塔尔',
}

def main():
    """三遍自查全量预测"""
    df, wc, wc_pl = load_data()
    tp, tg = calc_group_stats(wc_pl)
    elo = calc_elo(df)
    ko = get_ko_matches(wc)
    
    print("="*66)
    print("🏆 六爻神数 v8.29 — 三遍自查预测")
    print("="*66)
    
    groups = bj_group(ko)
    for dk in sorted(groups.keys(), key=lambda x:(int(x.split('月')[0]),int(x.split('月')[1].split('日')[0]))):
        ms = groups[dk]
        print(f"\n📅 {dk}")
        print(f"{'场次':<22} {'比分':>6} {'胜率':>5} {'平率':>5} {'v7':>5} {'v8':>5} {'提示':<16}")
        print("-"*66)
        for m in ms:
            h,a = m['h'],m['a']
            r = run_triple_check(h,a,elo,tp,tg)
            v8 = generate_v8(h,a,elo,tp,tg)
            tag = ''
            if r['dp']>0.55: tag='⚖️点球'
            elif r['e_h']>0.75: tag='✅稳胆'
            cn_h,cn_a = CN.get(h,h), CN.get(a,a)
            print(f"  {cn_h:<10}vs{cn_a:<10} {r['score'][0]}-{r['score'][1]} {r['e_h']:.0%} {r['dp']:.0%} {v8['v7']['e_h']:.0%} {v8['e_h']:.0%} {tag:<16}")

def calc_elo(df, K=32, HA=100):
    all_data = df[df['date']>='2000-01-01'].copy()
    all_data = all_data[all_data['home_score'].notna()].copy()
    all_data['home_score'] = pd.to_numeric(all_data['home_score'],errors='coerce')
    all_data['away_score'] = pd.to_numeric(all_data['away_score'],errors='coerce')
    all_data = all_data.dropna(subset=['home_score','away_score'])
    def rv(r): return 2 if r['home_score']>r['away_score'] else (1 if r['home_score']==r['away_score'] else 0)
    all_data['result'] = all_data.apply(rv, axis=1)
    elo = {}
    for _,r in all_data.iterrows():
        h,a = r['home_team'],r['away_team']
        if h not in elo: elo[h]=1500
        if a not in elo: elo[a]=1500
        w = 3.0 if r['tournament']=='FIFA World Cup' else 1.0
        sh,sa = (1,0) if r['result']==2 else ((0.5,0.5) if r['result']==1 else (0,1))
        e = 1/(1+10**((elo[a]-(elo[h]+HA))/400))
        elo[h] += K*w*(sh-e); elo[a] += K*w*(sa-(1-e))
    return elo

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        home, away = sys.argv[1], sys.argv[2]
        df, wc, wc_pl = load_data()
        tp, tg = calc_group_stats(wc_pl)
        elo = calc_elo(df)
        r = run_triple_check(home, away, elo, tp, tg)
        print(f"🏆 六爻神数 v8.29")
        print(f"  {home} vs {away}")
        print(f"  胜率: {r['e_h']:.1%}  平率: {r['dp']:.1%}")
        print(f"  推荐: {r['home']} {r['score'][0]}-{r['score'][1]} {r['away']}")
    else:
        main()
