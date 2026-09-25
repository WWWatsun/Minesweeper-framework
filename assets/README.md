Thư mục assets/ chỉ cần thiết khi chạy:
  - game/main.py (chơi bằng tay)
  - runner/run_agent.py --render (xem agent chơi trực quan)

Chạy benchmark headless (runner/run_agent.py, KHÔNG có --render) không cần assets/,
vì core/ và env/ không phụ thuộc pygame hay ảnh.
