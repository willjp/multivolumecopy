{ pkgs ? import <nixpkgs> {} }:

pkgs.stdenv.mkDerivation {
  pname = "multivolumecopy";
  version = "0.4.0";
  buildInputs = [
    pkgs.pipenv
    pkgs.python38
  ];
}
