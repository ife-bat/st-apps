# st-apps

Streamlit apps for battery researchers

## Structure

```shell
st-apps/
     Dockerfile
     src/
        Home.py
        pages/
            1_my_app.py
            2_second_app.py
            3_another_app.py
```

### Location on odin

`/usr/local/apps/st-apps`

## Methodology

1. update repository by adding another app as a .py file in the `st-apps/src/pages` directory (e.g. `4_the_best_app.py`)
2. go to st-apps location in odin and pull changes
3. re-build and run docker

## Running the docker image

```shell

docker buld -t streamlit-apps .

docker run -p 8501:8501 streamlit-apps

```
