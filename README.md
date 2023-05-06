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


## Developing and testing your sub-app

Assume your app is called `nice_app.py`. Put the app in the `pages` folder and change the name follwing this convention:

`<number>_<name>.py`

The `<number>` is used to order / position the short-cut to the app in the side-bar with the label `<name>`. For example,
if you call the file `000_Solve_equations.py`, the link `Solve equations` will most likely be put on top of the 
list of apps in the side-bar (first one below `Home`). 

## Update the local repository in odin

Log in to odin using ssh (either through a terminal or using the remote coding option in VSCode). Then go to / open
the directory and pull changes from the [github repository](https://github.com/ife-bat/st-apps.git).

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
docker buld -t streamlit-apps .

# run the docker container using the image:
docker run -p 8501:8501 streamlit-apps

```
