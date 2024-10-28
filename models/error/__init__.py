"""Exception"""
from .model import TournamentNotHaveInfoError, DatabaseError

CHESSRESULTS_CONNECT_ERROR_MSG = "Lỗi kết nối Chessresult!"
DATABASE_ERROR_MESSAGE = "Lỗi kết nối cơ sở dữ liệu!"
NOT_FOUND_CHESSRESULTS_XLSX_FILE_MESSAGE = "Không tìm thấy kết quả!"

__all__ = "TournamentNotHaveInfoError", "DatabaseError"
