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


# 檢查 Docker 標籤
## 如何確認 Docker 標籤是否存在

此部分說明如何使用 `check_docker_tag.py` 腳本來檢查特定的 Docker 標籤是否存在於 Docker Hub 上。這對於確保所需的映像檔可用性非常重要。

### 執行範例

以下範例展示如何檢查 `bitnami/os-shell` 映像檔的 `11-debian-11-r90` 標籤是否存在：

## Scan and Rename Helm Chart Images
`scan_then_rename.py` 是一個用於掃描 Helm 圖表中的 Docker 映像檔並重新命名的工具。此腳本會先執行 `scan_helm_images.py` 來檢查圖表中的映像檔標籤是否存在，然後在掃描成功的情況下，執行 `rename_bitnami_images.py` 來將映像檔的命名空間從 `bitnami` 變更為 `bitnamilegacy`。

### 使用方法

1. 執行 `scan_then_rename.py` 腳本，並指定 Helm 圖表的目錄路徑。
2. 腳本會先掃描指定目錄下的 Helm 圖表，檢查所有 Docker 映像檔標籤是否存在。
3. 如果掃描成功，腳本會將所有 `bitnami` 命名空間的映像檔重新命名為 `bitnamilegacy`。
4. 如果掃描失敗，腳本將跳過重新命名步驟。

### 執行範例

```bash
python3 scan_then_rename.py /root/app/manufacture/kafka/kafka
```