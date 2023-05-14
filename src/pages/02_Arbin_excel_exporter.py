import os
import pathlib
import tempfile

import streamlit as st
import cellpy


st.title("Arbin Excel Exporter :sunglasses:")
st.write("By IFE Battery Lab")

settings = st.expander("Cell information", expanded=True)
mass = settings.number_input("Mass (mg):", min_value=0.0001, max_value=5000.0, value=1.0)
nominal_capacity = settings.number_input(
    "Nominal capacity (mAh/g):", min_value=10.0, max_value=5000.0, value=372.0
)

raw_file = st.file_uploader("Upload raw file (*.res)", type=["res"])

button = st.button("Process file")

st.divider()
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
        file_type="arbin_res",
        mass=mass,
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
