"""
魔方 — 3D Rubik's Cube
（内部入口 — 请通过上级 main.py 运行）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.app import App


def main():
    app = App()
    app.run()


if __name__ == '__main__':
    main()
