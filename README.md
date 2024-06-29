# 1000ps-feed
Feed Generator for 1000PS Testberichte <https://www.1000ps.de/motorrad-testberichte>

## Upload configuration

> [!NOTE]
> If FTP_HOST is not configured, upload is skipped.  
> FTP_PATH is optional

Create a `.env` file in the root directory with the following content:

```
FTP_HOST = ftp-host
FTP_USER = username
FTP_PASS = password
FTP_PATH = target-path
```
