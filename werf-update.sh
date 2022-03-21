#!/bin/bash

source <(multiwerf use 1.0 alpha)

BIN=$(werf --path)

ln -snf ${BIN} ~/bin/werf
