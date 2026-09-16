import streamlit as st
import json
import os
import random
import urllib.parse
import pandas as pd
from datetime import datetime
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="阿信詩意歌詞策展台",
    page_icon="✨",
    layout="wide"
)

# File paths
RAW_DB_PATH = "ashin_lyrics_database.json"
FALLBACK_MASTER_PATH = "ashin_songs_master.json"
CURATED_DB_PATH = "curated_quotes.json"
CURATED_CSV_PATH = "curated_quotes.csv"
PROGRESS_DB_PATH = "songs_progress.json"

# Load Raw Database
@st.cache_data(ttl=5)
def load_raw_songs():
    path = RAW_DB_PATH if os.path.exists(RAW_DB_PATH) else FALLBACK_MASTER_PATH
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_curated_quotes():
    if os.path.exists(CURATED_DB_PATH):
        try:
            with open(CURATED_DB_PATH, 'r', encoding='utf-8') as f:
                quotes = json.load(f)
                for q in quotes:
                    if "rating" not in q:
                        q["rating"] = 3
                return quotes
        except Exception:
            return []
    return []

def load_song_progress():
    if os.path.exists(PROGRESS_DB_PATH):
        try:
            with open(PROGRESS_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_song_progress(progress_dict):
    with open(PROGRESS_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(progress_dict, f, ensure_ascii=False, indent=2)

def renumber_and_save(quotes):
    for idx, q in enumerate(quotes):
        q["day_number"] = idx + 1
        day_tag = f"Day{idx + 1}"
        lines = q.get("full_post_content", "").splitlines()
        if lines and "《一天一段阿信如詩一般的詞，直到下一場演唱會》" in lines[0]:
            lines[0] = f"《一天一段阿信如詩一般的詞，直到下一場演唱會》{day_tag}"
            q["full_post_content"] = "\n".join(lines)
            q["post_title"] = lines[0]
        else:
            q["post_title"] = f"《一天一段阿信如詩一般的詞，直到下一場演唱會》{day_tag}"

    with open(CURATED_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)
    if quotes:
        df = pd.DataFrame(quotes)
        df.to_csv(CURATED_CSV_PATH, index=False, encoding='utf-8-sig')
    else:
        if os.path.exists(CURATED_CSV_PATH):
            os.remove(CURATED_CSV_PATH)

def smart_shuffle_quotes(quotes):
    if len(quotes) <= 2:
        random.shuffle(quotes)
        return quotes

    groups = defaultdict(list)
    for q in quotes:
        key = (q.get("artist", ""), q.get("song_title", ""))
        groups[key].append(q)

    sorted_groups = sorted(groups.values(), key=len, reverse=True)
    all_items = []
    max_len = max(len(g) for g in sorted_groups)
    for g in sorted_groups:
        random.shuffle(g)

    for col in range(max_len):
        layer = [g[col] for g in sorted_groups if col < len(g)]
        random.shuffle(layer)
        all_items.extend(layer)

    for i in range(len(all_items) - 1):
        if (all_items[i].get("song_title") == all_items[i+1].get("song_title") and 
            all_items[i].get("artist") == all_items[i+1].get("artist")):
            for j in range(i + 2, len(all_items)):
                if (all_items[j].get("song_title") != all_items[i].get("song_title") and
                    (j == len(all_items) - 1 or all_items[j-1].get("song_title") != all_items[i].get("song_title"))):
                    all_items[i+1], all_items[j] = all_items[j], all_items[i+1]
                    break

    return all_items

# Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.95rem;
        opacity: 0.75;
        margin-bottom: 1.2rem;
    }
    .lyrics-box {
        background-color: rgba(255, 255, 255, 0.05);
        color: inherit;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 1.4rem;
        max-height: 540px;
        overflow-y: auto;
        font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif;
        line-height: 2;
        font-size: 1.05rem;
        white-space: pre-wrap;
    }
    .preview-card {
        background-color: #121212;
        border: 1px solid #262626;
        color: #F5F5F5;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .music-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #FF0000;
        color: white !important;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.88rem;
        font-weight: 600;
        margin-top: 4px;
        margin-right: 8px;
    }
    .music-btn:hover {
        background-color: #CC0000;
        text-decoration: none;
    }
    .music-btn-ytm {
        background-color: #282828;
    }
    .music-btn-ytm:hover {
        background-color: #3F3F3F;
    }
    .music-btn-kkbox {
        background-color: #00A3E0;
    }
    .music-btn-kkbox:hover {
        background-color: #0082B3;
    }
    .shuffle-box {
        background-color: rgba(99, 102, 241, 0.08);
        border: 1px dashed rgba(99, 102, 241, 0.4);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .manage-box {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Main App Layout
songs = load_raw_songs()
curated_quotes = load_curated_quotes()
song_progress = load_song_progress()

STATUS_TODO = "⚪ 未處理"
STATUS_PENDING = "🟡 待處理（已節錄，可能還有其他段落）"
STATUS_DONE = "🟢 已處理（已節錄完畢，不再新增）"

def get_song_key(s):
    return f"{s['artist']}___{s['clean_title']}"

def get_song_status(s):
    key = get_song_key(s)
    if key in song_progress:
        return song_progress[key]
    has_quotes = any(q.get("song_title") == s['clean_title'] and q.get("artist") == s['artist'] for q in curated_quotes)
    if has_quotes:
        return STATUS_PENDING
    return STATUS_TODO

status_counts = {STATUS_TODO: 0, STATUS_PENDING: 0, STATUS_DONE: 0}
for s in songs:
    st_val = get_song_status(s)
    status_counts[st_val] = status_counts.get(st_val, 0) + 1

# Sidebar: Filters & Song Selection
with st.sidebar:
    st.markdown("### 🗂️ 歌曲庫篩選")

    status_filter_options = [
        "全部狀態",
        f"⚪ 未處理 ({status_counts[STATUS_TODO]})",
        f"🟡 待處理 ({status_counts[STATUS_PENDING]})",
        f"🟢 已處理 ({status_counts[STATUS_DONE]})"
    ]
    selected_status_filter = st.selectbox("📌 處理狀態篩選", status_filter_options)

    all_cats = ["全部類別"] + sorted(list(set(s.get('category', '其它') for s in songs)))
    selected_cat = st.selectbox("選擇分類", all_cats)
    
    filtered_songs = songs
    if selected_cat != "全部類別":
        filtered_songs = [s for s in filtered_songs if s.get('category') == selected_cat]
        
    if "未處理" in selected_status_filter:
        filtered_songs = [s for s in filtered_songs if get_song_status(s) == STATUS_TODO]
    elif "待處理" in selected_status_filter:
        filtered_songs = [s for s in filtered_songs if get_song_status(s) == STATUS_PENDING]
    elif "已處理" in selected_status_filter:
        filtered_songs = [s for s in filtered_songs if get_song_status(s) == STATUS_DONE]

    search_keyword = st.text_input("🔍 搜尋歌名 / 歌手", "")
    if search_keyword:
        filtered_songs = [s for s in filtered_songs if search_keyword.lower() in s['clean_title'].lower() or search_keyword.lower() in s['artist'].lower()]
        
    st.markdown(f"**符合條件曲目：** `{len(filtered_songs)}` 首")
    
    def format_song_item(s):
        st_val = get_song_status(s)
        icon = "⚪" if st_val == STATUS_TODO else ("🟡" if st_val == STATUS_PENDING else "🟢")
        quotes_count = sum(1 for q in curated_quotes if q.get("song_title") == s['clean_title'] and q.get("artist") == s['artist'])
        q_info = f" [{quotes_count}段]" if quotes_count > 0 else ""
        return f"{icon} [{s['artist']}] 《{s['clean_title']}》{q_info}"

    if filtered_songs:
        filtered_keys = [get_song_key(s) for s in filtered_songs]
        default_index = 0
        if "active_song_key" in st.session_state and st.session_state["active_song_key"] in filtered_keys:
            default_index = filtered_keys.index(st.session_state["active_song_key"])

        selected_song_idx = st.selectbox(
            "選擇要策展的歌曲",
            range(len(filtered_songs)),
            index=default_index,
            format_func=lambda i: format_song_item(filtered_songs[i]),
            key="song_selector_widget"
        )
        current_song = filtered_songs[selected_song_idx]
        st.session_state["active_song_key"] = get_song_key(current_song)
    else:
        current_song = None

    st.markdown("---")
    st.markdown("### 📊 策展庫進度追蹤")
    total_saved = len(curated_quotes)
    st.metric("目前已收錄金句總數", f"{total_saved} 則")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        p_2y = min(1.0, total_saved / 730)
        st.caption(f"2年期 (730天): {p_2y*100:.1f}%")
        st.progress(p_2y)
    with c_p2:
        p_3y = min(1.0, total_saved / 1095)
        st.caption(f"3年期 (1095天): {p_3y*100:.1f}%")
        st.progress(p_3y)
        
    st.caption("🎯 目標：一天一則，直到下一場演唱會當天！")

    if total_saved > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = pd.DataFrame(curated_quotes).to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 匯出精選庫 CSV 表單",
            data=csv_data,
            file_name=f"mayday_ashin_quotes_Total{total_saved}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Header
col_header, col_status = st.columns([3, 1])
with col_header:
    st.markdown('<div class="main-title">✨ 阿信如詩歌詞 · 策展工作台</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">《一天一段阿信如詩一般的詞，直到下一場演唱會》每日貼文內容庫</div>', unsafe_allow_html=True)

if not current_song:
    st.warning("⚠️ 目前篩選條件下無符合歌曲。")
    st.stop()

current_song_key = get_song_key(current_song)
current_status = get_song_status(current_song)

existing_song_quotes = [q for q in curated_quotes if q.get("song_title") == current_song['clean_title'] and q.get("artist") == current_song['artist']]

# Build Music Search URLs
query_str = f"{current_song['artist']} {current_song['clean_title']}"
encoded_query = urllib.parse.quote(query_str)
yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"
ytm_url = f"https://music.youtube.com/search?q={encoded_query}"
kkbox_url = f"https://www.kkbox.com/tw/tc/search.php?word={encoded_query}"

# Work Area: Two columns (Left: Lyrics, Right: Selector & Preview)
col_left, col_right = st.columns([1.1, 1], gap="large")

# Left Column: Lyrics & Status Toggle
with col_left:
    c_ltitle, c_lstatus = st.columns([2, 1.4])
    with c_ltitle:
        st.markdown(f"### 🎵 《{current_song['clean_title']}》")
    with c_lstatus:
        status_options = [STATUS_TODO, STATUS_PENDING, STATUS_DONE]
        cur_idx = status_options.index(current_status) if current_status in status_options else 0
        new_status = st.selectbox(
            "📍 標記此曲處理進度：",
            status_options,
            index=cur_idx,
            key=f"status_select_{current_song_key}"
        )
        if new_status != current_status:
            song_progress[current_song_key] = new_status
            save_song_progress(song_progress)
            st.toast(f"已將《{current_song['clean_title']}》狀態更新為：{new_status.split()[1]}", icon="✅")
            st.rerun()

    meta_info = f"**歌手：** {current_song['artist']} ｜ **出處：** {current_song.get('album_or_year', '單曲/特別企劃')}"
    if current_song.get('notes'):
        meta_info += f" ｜ *{current_song['notes']}*"
    st.markdown(meta_info)

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <a href="{yt_url}" target="_blank" class="music-btn">▶️ YouTube 播放</a>
        <a href="{ytm_url}" target="_blank" class="music-btn music-btn-ytm">🎵 YouTube Music</a>
        <a href="{kkbox_url}" target="_blank" class="music-btn music-btn-kkbox">🎧 KKBOX 搜尋</a>
    </div>
    """, unsafe_allow_html=True)

    if existing_song_quotes:
        with st.expander(f"📌 本曲目前已收錄 {len(existing_song_quotes)} 個片段（點擊展開防重覆）", expanded=False):
            for eq in existing_song_quotes:
                st.markdown(f"- **Day{eq['day_number']}** ({'⭐'*eq.get('rating', 3)}): {eq['quote_text']}")

    lyrics_text = current_song.get('lyrics')
    if not lyrics_text:
        st.info("💡 此首歌詞尚未自動收錄，你可以手動在下方貼上：")
        lyrics_input = st.text_area("手動貼上/編輯歌詞", height=300, key=f"lyric_edit_{current_song['clean_title']}")
        if st.button("儲存這首歌的歌詞"):
            current_song['lyrics'] = lyrics_input
            for s in songs:
                if s['clean_title'] == current_song['clean_title'] and s['artist'] == current_song['artist']:
                    s['lyrics'] = lyrics_input
            with open(RAW_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(songs, f, ensure_ascii=False, indent=2)
            st.success("歌詞已儲存！")
            st.rerun()
        lyrics_lines = [l for l in lyrics_input.splitlines() if l.strip()] if lyrics_input else []
    else:
        lyrics_lines = [l.strip() for l in lyrics_text.splitlines() if l.strip()]
        st.markdown(f'<div class="lyrics-box">{lyrics_text}</div>', unsafe_allow_html=True)

# Right Column: Curator & Preview
with col_right:
    st.markdown("### ✍️ 挑選金句段落 (1～4 句)")
    
    if "quote_counter" not in st.session_state:
        st.session_state["quote_counter"] = 0
    
    multiselect_key = f"lines_{current_song_key}_{st.session_state['quote_counter']}"
    
    if lyrics_lines:
        selected_indices = st.multiselect(
            "點選要引用的歌詞行（依點選順序或行號排列）：",
            options=range(len(lyrics_lines)),
            format_func=lambda i: f"{i+1:02d}. {lyrics_lines[i]}",
            key=multiselect_key
        )
        
        if selected_indices:
            ordered_indices = sorted(selected_indices)
            picked_quote_text = "\n".join([lyrics_lines[idx] for idx in ordered_indices])
        else:
            picked_quote_text = ""
    else:
        selected_indices = []
        picked_quote_text = ""

    temp_day_num = len(curated_quotes) + 1
    
    header_line = f"《一天一段阿信如詩一般的詞，直到下一場演唱會》Day{temp_day_num}"
    quote_snippet = picked_quote_text.strip() if picked_quote_text.strip() else "（請在上方勾選或在此編輯節錄歌詞）"
    body_quote_line = f"＂{quote_snippet}＂ ── {current_song['artist']}《{current_song['clean_title']}》"
    tags_line = "#五月天 #阿信"
    
    default_full_post = f"{header_line}\n\n{body_quote_line}\n\n{tags_line}"
    
    editor_key = f"post_editor_{current_song_key}_{st.session_state['quote_counter']}"
    
    if editor_key not in st.session_state:
        st.session_state[editor_key] = default_full_post

    if "last_picked_quote" not in st.session_state:
        st.session_state["last_picked_quote"] = ""
    if picked_quote_text != st.session_state["last_picked_quote"]:
        st.session_state[editor_key] = default_full_post
        st.session_state["last_picked_quote"] = picked_quote_text

    st.markdown("#### 📱 Threads 貼文預覽與完整編輯")
    st.caption("💡 採集階段只管挑選，後續可在下方隨時【一鍵智能打亂】，避免同首歌連續出現！")
    
    edited_post_content = st.text_area(
        "Threads 發文完整內容：",
        key=editor_key,
        height=175
    )

    st.markdown(f"""
    <div class="preview-card">
        <div style="font-size: 1.05rem; line-height: 1.85; white-space: pre-wrap; color: #FFFFFF;">{edited_post_content}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_rating_input, col_action_btn = st.columns([1.1, 1.9])
    
    with col_rating_input:
        quote_rating = st.selectbox(
            "⭐ 此段推薦度：",
            [3, 2, 1],
            format_func=lambda r: "⭐⭐⭐ 極力推薦" if r == 3 else ("⭐⭐ 值得分享" if r == 2 else "⭐ 備選參考"),
            key=f"rating_select_{current_song_key}_{st.session_state['quote_counter']}",
            label_visibility="collapsed"
        )
    
    with col_action_btn:
        if st.button("🌟 收錄此段落至【精選庫存池】", type="primary", use_container_width=True):
            if not edited_post_content.strip() or "（請在上方勾選" in edited_post_content:
                st.error("請先在上方挑選歌詞段落！")
            else:
                new_entry = {
                    "day_number": temp_day_num,
                    "post_title": header_line,
                    "song_title": current_song['clean_title'],
                    "artist": current_song['artist'],
                    "album_or_year": current_song.get('album_or_year', ''),
                    "quote_text": picked_quote_text.strip(),
                    "full_post_content": edited_post_content.strip(),
                    "rating": quote_rating,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "ready_to_post"
                }
                curated_quotes.append(new_entry)
                renumber_and_save(curated_quotes)
                
                if current_status == STATUS_TODO:
                    song_progress[current_song_key] = STATUS_PENDING
                    save_song_progress(song_progress)
                    
                st.session_state["active_song_key"] = current_song_key
                st.session_state["quote_counter"] += 1
                st.session_state["last_picked_quote"] = ""
                
                stars_str = "⭐" * quote_rating
                st.toast(f"🎉 成功收錄《{current_song['clean_title']}》（評分：{stars_str}）！繼續挑選下一段。", icon="🌟")
                st.rerun()

# Bottom Section: Smart Shuffle & Curated Quotes Table
st.markdown("---")

if curated_quotes:
    st.markdown('<div class="shuffle-box">', unsafe_allow_html=True)
    c_shuf1, c_shuf2 = st.columns([2.5, 1])
    with c_shuf1:
        st.markdown("#### 🎲 智能分散打亂（避免同首歌連著發）")
        st.caption("採集時您可以盡情把同一首歌的所有金句都摘錄下來。點擊右方按鈕，演算法會**自動將同歌手、同歌曲的金句交錯打散拉開**，並一口氣將編號依序重新命名為 Day1, Day2, Day3...！")
    with c_shuf2:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("🔀 智能打亂並重新排序 Day1~N", type="primary", use_container_width=True):
            shuffled = smart_shuffle_quotes(curated_quotes)
            renumber_and_save(shuffled)
            st.toast("🎉 智能打亂完成！同首歌金句已完美交錯拉開，編號已重新更新！", icon="✨")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Search & Filter bar for Curated Table
    st.markdown("### 📋 目前已收錄的精選金句清單 (發文總表)")
    
    # Operations Bar: Re-rate & Delete in a clean manage box
    st.markdown('<div class="manage-box">', unsafe_allow_html=True)
    c_mgr_label, c_mgr_select, c_mgr_rate, c_mgr_rate_btn, c_mgr_del_btn = st.columns([1, 2.5, 1.2, 1, 1])
    
    with c_mgr_label:
        st.markdown("**⚙️ 段落管理：**")
        
    manage_options = [f"Day{q['day_number']} - {q['artist']}《{q['song_title']}》 ({'⭐'*q.get('rating', 3)})" for q in curated_quotes]
    
    with c_mgr_select:
        selected_manage_idx = st.selectbox(
            "選擇要調整的項目：",
            range(len(manage_options)),
            format_func=lambda i: manage_options[i],
            label_visibility="collapsed",
            key="manage_item_select"
        )
        
    target_quote = curated_quotes[selected_manage_idx]
    
    with c_mgr_rate:
        new_rerate_val = st.selectbox(
            "修改評分：",
            [3, 2, 1],
            index=[3, 2, 1].index(target_quote.get("rating", 3)),
            format_func=lambda r: "⭐⭐⭐ (3星)" if r == 3 else ("⭐⭐ (2星)" if r == 2 else "⭐ (1星)"),
            label_visibility="collapsed",
            key="rerate_select"
        )
        
    with c_mgr_rate_btn:
        if st.button("⭐ 更新評分", use_container_width=True):
            target_quote["rating"] = new_rerate_val
            renumber_and_save(curated_quotes)
            st.toast(f"✅ 已將 Day{target_quote['day_number']} 評分更新為 {'⭐'*new_rerate_val}！", icon="⭐")
            st.rerun()
            
    with c_mgr_del_btn:
        if st.button("🗑️ 刪除", type="secondary", use_container_width=True):
            deleted_item = curated_quotes.pop(selected_manage_idx)
            renumber_and_save(curated_quotes)
            st.warning(f"已刪除 Day{deleted_item['day_number']}（已重新排列剩餘天數序號）。")
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

    # Search and Filter Inputs
    c_s1, c_s2 = st.columns([2, 2])
    with c_s1:
        table_search = st.text_input("🔍 搜尋庫存中特定歌名 / 歌手 / 歌詞關鍵字：", "", placeholder="例如輸入：如煙、五月天、夏天...")
    with c_s2:
        rating_filter = st.radio(
            "篩選清單評分：",
            ["全部評分", "⭐⭐⭐ (3星)", "⭐⭐ (2星以上)", "⭐ (1星)"],
            horizontal=True
        )

    filtered_quotes = curated_quotes
    
    if table_search.strip():
        kw = table_search.strip().lower()
        filtered_quotes = [
            q for q in filtered_quotes 
            if kw in q.get("song_title", "").lower() 
            or kw in q.get("artist", "").lower() 
            or kw in q.get("quote_text", "").lower()
            or kw in q.get("full_post_content", "").lower()
        ]

    if rating_filter == "⭐⭐⭐ (3星)":
        filtered_quotes = [q for q in filtered_quotes if q.get("rating", 3) == 3]
    elif rating_filter == "⭐⭐ (2星以上)":
        filtered_quotes = [q for q in filtered_quotes if q.get("rating", 3) >= 2]
    elif rating_filter == "⭐ (1星)":
        filtered_quotes = [q for q in filtered_quotes if q.get("rating", 3) == 1]

    display_data = []
    for q in filtered_quotes:
        stars = "⭐" * q.get("rating", 3)
        display_data.append({
            "天數 (Day)": f"Day{q['day_number']}",
            "評分": stars,
            "歌名": q["song_title"],
            "演唱者": q["artist"],
            "Threads 完整貼文內容 (已排序)": q["full_post_content"],
            "收錄時間": q["created_at"]
        })

    if display_data:
        st.caption(f"共找到 **{len(display_data)}** 筆符合條件的金句：")
        df_curated = pd.DataFrame(display_data)
        st.dataframe(df_curated, use_container_width=True, height=320)
    else:
        st.info("查無符合搜尋或評分條件的金句。")
else:
    st.markdown("### 📋 目前已收錄的精選金句清單 (發文總表)")
    st.info("目前精選庫還是空的，快挑選第一首喜歡的歌詞加入吧！")