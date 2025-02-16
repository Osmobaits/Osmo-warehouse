{ pkgs }: {
    deps = [
      pkgs.python39
      pkgs.python39Packages.flask
      pkgs.python39Packages.flask_sqlalchemy
      pkgs.python39Packages.gunicorn
    ];
  }
