{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    (pkgs.python313.withPackages (ps: with ps; [
      pandas numpy scipy statsmodels plotly kaleido openpyxl xlsxwriter python-docx
    ]))
    pkgs.libreoffice
  ];
}
