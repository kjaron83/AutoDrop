# Create the python environment

## Setup Miniconda
https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install

## Create the environment
<pre>conda create --prefix ./env python=3.12</pre>

## Activate the environment
<pre>conda activate ./env</pre>

## Install requirements
<pre>
conda install fastapi
conda install uvicorn-standard
conda install jinja2
conda install python-multipart
conda install sqlalchemy
conda install alembic
conda install pymysql
conda install pytest
conda install httpx
conda install -c conda-forge fastapi-mail
conda install babel
</pre>

## Add project to the side packages
<pre>
conda install conda-build
conda-develop .
</pre>
