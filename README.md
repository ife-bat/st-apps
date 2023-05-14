# st-apps

Streamlit apps for battery researchers

## Structure

```shell
st-apps/
     Dockerfile
     README.md
     requirements.txt
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


## Developing and testing your sub-app

First clone (or pull recent changes from) the [github repository (ife-bat/st-apps)](https://github.com/ife-bat/st-apps.git).
Create a python environment and install requirements if you don't already have one.

Assume your app is called `my_eq_solv_v1.py`. Put the app in the `pages` folder and change the name follwing this convention:

`<number>_<name>.py`

The `<number>` is used to order / position the short-cut to the app in the side-bar with the label `<name>`. For example,
if you call the file `000_Solve_equations.py`, the link `Solve equations` will most likely be put on top of the 
list of apps in the side-bar (first one below `Home`). 

You can check if it works as intended by running the multipage app locally:

```shell
# in the top directory
streamlit run src/Home.py
```

If you want to check only your own app, point streamlit to your apps python-file.

```shell
# in the top directory
streamlit run src/pages/000_Solve_equations.py
```

## Update the local repository in odin

Log in to odin using ssh (either through a terminal or using the remote coding option in VSCode). Then go to / open
the directory and pull changes from the [github repository (ife-bat/st-apps)](https://github.com/ife-bat/st-apps.git).

```shell
cd /usr/local/apps/st-apps
git pull 
```


## Running the docker image

```shell

# (otional) stop the current docker container
docker ps  # to get the container_id
docker stop <container_id>


# (re-) build the docker image:
docker build -t streamlit-apps .

# run the docker container using the image:
docker run -d -p 8501:8501 streamlit-apps

```

## TODO

1. Split requirements into two files - one that contains the packages we believe will (almost) never change, and one for the others. This will speed up building the Docker container.
2. Use docker compose (create `docker-compose.yml`)
