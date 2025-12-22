{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {inherit system;};
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = with pkgs; [
        # we need firefox as we use it in selenium
        firefox
        # minimal python
        python313
        python313Packages.pip
        python313Packages.virtualenv
      ];
      shellHook = ''
        python --version
        virtualenv .venv
        source .venv/bin/activate
        # all the projects python dependencies will come from requirements.txt
        pip install -r requirements.txt
      '';
    };
  };
}
