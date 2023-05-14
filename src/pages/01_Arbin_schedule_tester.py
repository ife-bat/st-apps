from libs import arbin_schedule_tester_lib as ast
import streamlit as st
import bokeh.plotting as bplt

cell_type_options = {"Auto" : None,
                      "Anode half-cell" : "half_cell", 
                      "Cathode half-cell LFP" : "full_cell_LFP", 
                      "Cathode half-cell NMC" : "full_cell_NMC", 
                      "Full-cell with LFP" : "full_cell_LFP", 
                      "Full-cell with NMC" : "full_cell_NMC"}

tester = ast.Tester()

if "layout" not in st.session_state:
    st.session_state["layout"] = "grid"
if "fig_width" not in st.session_state:
    st.session_state["fig_width"] = 875
if "fig_height" not in st.session_state:
    st.session_state["fig_height"] = 500
if "new_tab" not in st.session_state:
    st.session_state["new_tab"] = False


st.set_page_config(layout="wide")
st.title("Arbin schedule tester")
st.write("By Asbjørn Ulvestad")

widget = st.container()
plotcontainer = st.container()
plotcontainer.empty()

uploaded_schedule = widget.file_uploader("Upload schedule file (*.sdu, *.sdx)", type=["sdu","sdx"])

#Make settings columns
col1, col2 = widget.columns(2)

#Populate main settings column
setting_expander = col1.expander("Test parameters", expanded=True)
cell_type_option = setting_expander.selectbox("Cell type:", 
                                          cell_type_options.keys())
max_cycles = setting_expander.number_input("Number of cycles to run:", 
                                           min_value=1, 
                                           max_value=5000, 
                                           value=100)

#Populate advanced settings column
advanced_setting_expander = col2.expander("Advanced settings", expanded=True)
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
progress_bar = widget.progress(0, "")

def updateplot():
    print("Drawing figure with")
    print("Width:", st.session_state["fig_width"])
    print("Height", st.session_state["fig_height"])
    print("Layout", st.session_state["layout"])
    print("New tab", st.session_state["new_tab"])
    if st.session_state["new_tab"]:
        plot = st.session_state["tester"].make_overview_bokeh(fig_width=st.session_state["fig_width"]*2, fig_height=st.session_state["fig_height"]*2, line_width=1.5, line_alpha=0.9, show_plot=True, normalize=True, vertical_stack=(st.session_state["layout"].lower()=="vertical"))
        bplt.show(plot)
    else:
        plot = st.session_state["tester"].make_overview_bokeh(fig_width=st.session_state["fig_width"]*2, fig_height=st.session_state["fig_height"]*2, line_width=1.5, line_alpha=0.9, show_plot=False, normalize=True, vertical_stack=(st.session_state["layout"].lower()=="vertical"))
        plotcontainer.bokeh_chart(plot, use_container_width=False)
    
if uploaded_schedule is not None and not button:
    progress_bar.progress(0, "Ready to run...")
if uploaded_schedule is None and button:
    progress_bar.progress(0, "Upload schedule before running!")
elif uploaded_schedule is not None and button:
    cellType = cell_type_options[cell_type_option]    
    progress_bar.progress(0, "Schedule is being interpreted...")
    schedule_bytes = uploaded_schedule.read()
    schedule_text = schedule_bytes.decode('utf-8', errors="ignore")
    schedule_lines = schedule_text.splitlines()


    tester.set_schedule(schedule_lines=schedule_lines)
    tester.build_cell(0.002, 1.000, delta_time=delta_time, cell_type=cellType, soc_length=soc_length)
    tester.run_test(max_cycles=max_cycles, progress_bar=progress_bar)
    
    progress_bar.progress(1.0, "Preparing figure")
    tester.prepare_output()
    st.session_state["tester"] = tester
    updateplot()
    # plot = tester.make_overview_bokeh(fig_width=1200*2, fig_height=1200, line_width=1.5, line_alpha=0.9, show_plot=False, normalize=True, vertical_stack=True)
    # widget.bokeh_chart(plot, use_container_width=False)
    progress_bar.progress(1.0, "Done")


if 'tester' in st.session_state:
    with widget.form("fig_params"):
        st.write("Figure parameters")
        subcol1, subcol2, subcol3 = st.columns(3)
        subcol1.selectbox("Figure layout:",
                     ["Grid",
                     "Vertical"],
                     index=0,
                     key="layout")
        subcol2.number_input("Plot width:",
                        min_value=100,
                        max_value=5000,
                        value=st.session_state["fig_width"],
                        key="fig_width")
        subcol3.number_input("Plot height:",
                        min_value=100,
                        max_value=5000,
                        value=st.session_state["fig_height"],
                        key="fig_height")
        # st.checkbox("Open in new tab",
        #                  value=False,
        #                  key="new_tab")
        st.form_submit_button("Redraw", on_click=updateplot)