import os
import pathlib
import tempfile

import streamlit as st
import cellpy


st.title("Arbin Excel Exporter :sunglasses:")
st.write("By Jan Petter Maehlen, IFE")


# --- Settings ---
settings = st.expander("Cell information", expanded=True)

mass = settings.number_input("Mass (mg):", min_value=0.0001, max_value=5000.0, value=1.0)
nominal_capacity = settings.number_input(
    "Nominal capacity (mAh/g):", min_value=10.0, max_value=5000.0, value=372.0
)
cycle_mode = settings.selectbox("Cycle mode:", ["anode-half-cell", "other"])
area = settings.number_input("Area (cm2):", min_value=0.0001, max_value=5000.0, value=1.0)

# TODO: add option for selecting other file types (cellpy-files and .h5 from arbin5)
raw_file_type = "arbin_res"
raw_file_extension = "res"

# --- Upload file ---
raw_file = st.file_uploader(f"Upload raw file (*.{raw_file_extension})", type=[raw_file_extension])
button = st.button("Process file")

st.divider()

# --- Process file ---
if raw_file is not None and button:
    progress_bar = st.progress(0.0, "Reading file ...")
    raw_bytes = raw_file.read()

    progress_bar.progress(0.1, "Reading file ...")
    raw_file_name = raw_file.name
    temporary_directory = pathlib.Path(tempfile.gettempdir())
    tmp_raw_file = temporary_directory / raw_file_name
    tmp_xlsx_file = tmp_raw_file.with_suffix(".xlsx")

    with open(tmp_raw_file, "wb") as f:
        f.write(raw_bytes)

    progress_bar.progress(0.3, "Reading file ...")
    c = cellpy.get(
        tmp_raw_file,
        instrument=raw_file_type,
        mass=mass,
        area=area,
        cycle_mode=cycle_mode,
        nominal_capacity=nominal_capacity,
        refuse_copying=True,
    )

    progress_bar.progress(0.5, "File is being interpreted...")
    c.to_excel(tmp_xlsx_file)
    with open(tmp_xlsx_file, "rb") as f:
        tmp_xlsx_bytes = f.read()

    progress_bar.progress(1.0, "Done!")

    st.write("Download file:")
    st.download_button(
        label="Download",
        data=tmp_xlsx_bytes,
        file_name=tmp_xlsx_file.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
