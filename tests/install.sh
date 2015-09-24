#!/usr/bin/env bash
# Setup travis for testing

build_p7zip() {
    local filename url
    url="http://sourceforge.net/projects/p7zip/files/p7zip/9.38.1/"
    url="${url}p7zip_9.38.1_src_all.tar.bz2/download"
    filename='p7z.tar.bz2'
    wget -O "$filename" "$url"
    tar -xf "$filename"

    pushd p7z*
    cp -f makefile.linux_any_cpu makefile.machine
    rm -rf DOC
    make 7z
    make DEST_HOME=$DEPS install
    popd
    rm -rf p7z*
}

build_unrar() {
    local filename url
    url="http://www.rarlab.com/rar/unrarsrc-5.3.4.tar.gz"
    filename='unrar.tar.gz'
    wget -O "$filename" "$url"
    tar -xf "$filename"

    pushd unrar*
    make unrar
    make DESTDIR=$DEPS install
    popd
    rm -rf unrar*
}

build_p7zip
build_unrar
