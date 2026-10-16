{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    (pkgs.python313.withPackages (ps: with ps; [
      pandas numpy scipy statsmodels plotly openpyxl xlsxwriter
    ]))
    pkgs.libreoffice
  ];
}
