from . import main
from flask import request, jsonify, redirect, url_for, Flask, send_from_directory, flash, render_template
import re

@main.route('/', methods=['GET', 'POST'])
def hello_world():
    return 'hello'
    
