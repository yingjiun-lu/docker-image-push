# docker-image-push
> Infortrend tools
## 簡介

`docker-image-push` 是一個用於處理 Docker 映像檔的工具。它可以從指定的來源命名空間拉取映像檔，重新標記為目標命名空間，並推送到 Docker registry。

## 使用方法

### 參數

- `--source-namespace`：來源命名空間的前綴（預設為 `'bitnami'`）。
- `--target-namespace`：目標命名空間的前綴（預設為 `'infortrend'`）。
- `--images-file`：包含映像檔列表的檔案路徑（每行一個映像檔）。如果未提供，將使用內建的預設列表。
- `--no-pull`：不在標記前拉取映像檔（僅標記）。

### 執行範例
1. 執行 `pull_and_tag.py` 腳本，並指定來源命名空間和目標命名空間。
2. 如果提供了 `--images-file` 參數，從指定的檔案中讀取映像檔列表；否則，使用內建的預設列表。
3. 對於每一個映像檔：
   - 嘗試建立目標映像檔名稱，若失敗則跳過該映像檔。
   - 如果未指定 `--no-pull` 參數，執行 `docker pull` 以拉取來源映像檔。
   - 執行 `docker tag` 以將來源映像檔重新標記為目標映像檔。
   - 執行 `docker push` 以推送目標映像檔到 Docker registry。
4. 對於每一個映像檔：
   - 嘗試建立目標映像檔名稱，若失敗則跳過該映像檔。
   - 執行 `docker rmi` 以移除來源映像檔。
   - 執行 `docker rmi` 以移除目標映像檔。
5. 如果有任何步驟失敗，將顯示錯誤訊息並繼續處理下一個映像檔。
6. 完成所有映像檔的處理後，顯示成功或失敗的總結訊息。

```bash
python pull_and_tag.py --source-namespace bitnami --target-namespace infortrend
```

## 注意事項

- 在執行前，請確保 Docker 已經安裝並正在運行。
- 如果未提供 `--images-file` 參數，將使用內建的預設列表。
- 如果未提供 `--no-pull` 參數，將在標記前拉取映像檔。


