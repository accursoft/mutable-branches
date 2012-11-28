@echo off
call tests > tests.actual 2>&1
fc tests.actual tests.expected
del tests.actual