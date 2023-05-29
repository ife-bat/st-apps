import os
import pathlib
import tempfile

import streamlit as st
import cellpy


st.title("Arbin Excel Exporter :sunglasses:")
st.write("By Jan Petter Maehlen, IFE")


# --- Settings ---
settings = st.expander("Cell information", expanded=True)
cycles = st.checkbox("Export voltage-curves", value=False)
raw = st.checkbox("Export raw-data", value=False)
st.write(":warning: Exporting raw-data and/or cycles might take several minutes to perform.")
nom_cap_specifics = settings.selectbox("Specific: ", ["gravimetric", "areal"])
cycle_mode = settings.selectbox("Cycle mode:", ["standard", "anode",], help="select anode if you are testing anode in half-cell configuration")
mass = settings.number_input("Mass (mg):", min_value=0.0001, max_value=5000.0, value=1.0)
nominal_capacity = settings.number_input(
    "Nominal capacity (mAh/g):", min_value=10.0, max_value=5000.0, value=372.0
)

area = settings.number_input("Area (cm2):", min_value=0.0001, max_value=5000.0, value=1.0)

# TODO: add option for selecting other file types (cellpy-files and .h5 from arbin5)
raw_file_type = "arbin_res"
raw_file_extension = "res"

# --- Upload file ---
raw_file = st.file_uploader(
    f"Upload raw file(s) (*.{raw_file_extension})", 
    type=[raw_file_extension], 
    accept_multiple_files=True
)
button = st.button("Process file(s)")

st.divider()

# --- Process file ---
if raw_file is not None and button:
    temporary_directory = pathlib.Path(tempfile.gettempdir())
    files = [p.name for p in raw_file]
    number_of_files = len(files)
    delta = 0.3 / number_of_files
    tmp_file_names = [temporary_directory / p.name for p in raw_file]

    progress_bar = st.progress(0.0, "Reading file(s) ...")

    tmp_xlsx_file = tmp_file_names[0].with_suffix(".xlsx")
    if len(tmp_file_names) > 1:
        tmp_xlsx_file = tmp_xlsx_file.with_name(tmp_xlsx_file.stem + "_and_more.xlsx")

    for i, (f, t) in enumerate(zip(raw_file, tmp_file_names)):
        progress_bar.progress(i * delta, f"Reading file {i} ...")
        raw_bytes = f.read()
        with open(t, "wb") as b:
            b.write(raw_bytes)

    progress_bar.progress(0.4, "Processing file(s) ...")
    tmp_file_names = sorted(tmp_file_names)

    # TODO: split this up into two steps (read and make summary)
    c = cellpy.get(
        tmp_file_names,
        instrument=raw_file_type,
        mass=mass,
        area=area,
        cycle_mode=cycle_mode,
        nom_cap_specifics=nom_cap_specifics,
        nominal_capacity=nominal_capacity,
        refuse_copying=True,
    )

    if cycles:
        progress_bar.progress(0.5, "Extracting cycles and converting ...")
    else:
        progress_bar.progress(0.5, "Converting ...")
    c.to_excel(tmp_xlsx_file, raw=raw, cycles=cycles)

    progress_bar.progress(0.9, "Wrapping up ...")
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
