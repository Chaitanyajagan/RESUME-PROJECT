"""
UI Styles & Visual Components for EDUKRON ATS Streamlit Application.
Contains responsive dark-theme CSS and interactive SVG Progress Wheel.
"""

import streamlit as st

def apply_custom_styles():
    """Injects high-contrast dark theme styling and hides default sidebars."""
    st.markdown("""
    <style>
        /* Global Titles */
        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #F8FAFC;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            font-size: 1.05rem;
            color: #94A3B8;
            margin-bottom: 1.5rem;
        }
        /* Dynamic Page Header Banner */
        .page-banner {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .page-banner-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #F8FAFC;
        }
        .page-banner-desc {
            font-size: 0.88rem;
            color: #94A3B8;
        }
        /* Candidate Card */
        .candidate-card {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            color: #F8FAFC;
            transition: border-color 0.15s ease-in-out;
        }
        .candidate-card:hover {
            border-color: #3B82F6;
        }
        /* Skill Badges */
        .skill-tag {
            display: inline-block;
            background-color: rgba(37, 99, 235, 0.25);
            color: #93C5FD;
            border: 1px solid rgba(59, 130, 246, 0.4);
            padding: 3px 8px;
            margin: 2px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .missing-tag {
            display: inline-block;
            background-color: rgba(239, 68, 68, 0.25);
            color: #FCA5A5;
            border: 1px solid rgba(239, 68, 68, 0.4);
            padding: 3px 8px;
            margin: 2px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        /* Dynamic Navigation Stepper */
        .nav-step {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
        }
        /* Hide Default Sidebar Completely */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_phase_wheel(current_stage_num: int):
    """
    Renders an SVG Progress Wheel dynamically reflecting the active workflow stage.
    """
    stages = [
        (1, "Resume Intake & OCR", 25),
        (2, "JD Query & Dense Search", 50),
        (3, "Ranking & Assessment", 75),
        (4, "Gmail Dispatch & Calendly", 100)
    ]
    
    current_info = stages[current_stage_num - 1]
    progress_percent = current_info[2]
    
    # SVG circle calculation
    radius = 36
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference - (progress_percent / 100.0) * circumference
    
    wheel_svg = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: #1E293B; border: 1px solid #334155; border-radius: 14px; padding: 14px 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); margin-bottom: 22px; color: #F8FAFC;">
        <div style="display: flex; align-items: center; gap: 18px;">
            <div style="position: relative; width: 84px; height: 84px; display: flex; align-items: center; justify-content: center;">
                <svg width="84" height="84" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="{radius}" stroke="#334155" stroke-width="8" fill="none" />
                    <circle cx="50" cy="50" r="{radius}" stroke="#3B82F6" stroke-width="8" fill="none"
                            stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}"
                            stroke-linecap="round" style="transition: stroke-dashoffset 0.5s ease;"
                            transform="rotate(-90 50 50)" />
                </svg>
                <div style="position: absolute; text-align: center;">
                    <span style="font-size: 16px; font-weight: 800; color: #F8FAFC;">{progress_percent}%</span>
                </div>
            </div>
            <div>
                <div style="font-size: 11px; font-weight: 700; color: #60A5FA; text-transform: uppercase; letter-spacing: 0.6px;">ACTIVE WORKFLOW STAGE</div>
                <div style="font-size: 18px; font-weight: 800; color: #FFFFFF;">Stage {current_stage_num} of 4: {current_info[1]}</div>
                <div style="font-size: 12px; color: #94A3B8;">EDUKRON Capstone Architecture • Production Outbox Gate</div>
            </div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end;">
    """
    
    for num, name, _ in stages:
        if num == current_stage_num:
            wheel_svg += f"""<span style="background: #2563EB; color: white; padding: 6px 14px; border-radius: 14px; font-size: 12px; font-weight: 700; box-shadow: 0 0 10px rgba(37, 99, 235, 0.5);">● {num}. {name}</span>"""
        elif num < current_stage_num:
            wheel_svg += f"""<span style="background: rgba(37, 99, 235, 0.2); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.4); padding: 6px 12px; border-radius: 14px; font-size: 12px; font-weight: 600;">✓ {num}. {name}</span>"""
        else:
            wheel_svg += f"""<span style="background: #334155; color: #CBD5E1; border: 1px solid #475569; padding: 6px 12px; border-radius: 14px; font-size: 12px;">{num}. {name}</span>"""
            
    wheel_svg += """
        </div>
    </div>
    """
    st.markdown(wheel_svg, unsafe_allow_html=True)
