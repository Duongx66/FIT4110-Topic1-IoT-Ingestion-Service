# Evidence Buổi 02

Thư mục này lưu bằng chứng Lab 02.

Cần có:

```text
evidence/buoi-02/
  README.md
  checklist.md
  known-issues.md
  spectral-report.txt
  tool-versions.txt
  git-log.txt
  mock-screenshots/
    req-01-*.txt
    req-02-*.txt
    req-03-*.txt
    req-04-*.txt
    req-05-*.txt
```

## Cách sinh report Spectral

```bash
./scripts/collect_session02_evidence.sh
```

Windows:

```powershell
.\scripts\collect_session02_evidence.ps1
```

## Ảnh mock server

Lab 02 chưa yêu cầu Postman. Minh chứng nên là ảnh chụp Terminal/PowerShell khi chạy `curl` tới Prism mock server.

Trong môi trường này, các request mẫu đã được lưu tại `evidence/buoi-02/mock-screenshots/` dưới dạng file log văn bản để chứng minh lệnh, status code và response body.

Mỗi file log chứa:

- lệnh `curl` đã gọi;
- status code;
- response body;
- URL `http://localhost:4010/...`.
