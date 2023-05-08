from libs import arbin_schedule_tester_lib as ast
import streamlit as st

cell_type_options = {"Auto" : None,
                      "Anode half-cell" : "half_cell", 
                      "Cathode half-cell LFP" : "full_cell_LFP", 
                      "Cathode half-cell NMC" : "full_cell_NMC", 
                      "Full-cell with LFP" : "full_cell_LFP", 
                      "Full-cell with NMC" : "full_cell_NMC"}


st.set_page_config(layout="wide")
st.title("Arbin schedule tester")
st.write("By Asbjørn Ulvestad")

#Make settings columns
col1, col2, col3 = st.columns(3)

#Populate main settings column
st.session_state["setting_expander_state"] = True
uploaded_schedule = col1.file_uploader("Upload schedule file (*.sdu, *.sdx)", type=["sdu","sdx"])
setting_expander = col2.expander("Test parameters", expanded=False)
cell_type_option = setting_expander.selectbox("Cell type:", 
                                          cell_type_options.keys())
max_cycles = setting_expander.number_input("Number of cycles to run:", 
                                           min_value=1, 
                                           max_value=5000, 
                                           value=100)

#Populate advanced settings column
advanced_setting_expander = col3.expander("Advanced settings", expanded=False)
delta_time =  advanced_setting_expander.number_input("Delta time:", 
                                                     min_value=0.1, 
                                                     max_value=5.0, 
                                                     value=1.0,
                                                     )
soc_length = advanced_setting_expander.number_input("Number of elements in thin film model:",
                                                    min_value=5,
                                                    max_value=100,
                                                    value=20)
button = col1.button("Run test")


if uploaded_schedule is not None and button:
    cellType = cell_type_options[cell_type_option]    
    schedule_bytes = uploaded_schedule.read()
    schedule_text = schedule_bytes.decode('utf-8', errors="ignore")
    schedule_lines = schedule_text.splitlines()

    progress_bar = st.progress(0, "Schedule is being interpreted...")

    tester = ast.Tester()
    tester.set_schedule(schedule_lines=schedule_lines)
    tester.build_cell(0.002, 1.000, delta_time=delta_time, cell_type=cellType, soc_length=soc_length)
    tester.run_test(max_cycles=max_cycles, progress_bar=progress_bar)
    progress_bar.progress(1.0, "Done")


    tester.prepare_output()

    plot = tester.make_overview_bokeh(fig_width=2300, fig_height=1000, line_width=1.5, line_alpha=0.9, show_plot=False, normalize=True)
    ct = st.empty()
    ct.bokeh_chart(plot, use_container_width=False)

