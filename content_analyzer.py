import os
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 監視対象のディレクトリ（サブディレクトリも含めて再帰的に監視します）
WATCH_DIR = Path("./target_folder")

class FileRenameHandler(FileSystemEventHandler):
    def on_created(self, event):
        # ディレクトリの作成や、一時ファイル・ダウンロード中のファイルは処理対象外とします
        if event.is_directory or event.src_path.endswith(('.tmp', '.crdownload', '.part')):
            return
        
        file_path = Path(event.src_path)
        print(f"新しくファイルを検知しました: {file_path}")
        
        # ファイルへの書き込みが完全に完了するまで少し待機します
        time.sleep(1.0)
        
        # ファイルが実際に存在するか確認（競合を防ぐため）
        if not file_path.exists():
            return
        
        try:
            self.process_and_rename(file_path)
        except Exception as e:
            print(f"エラーが発生しました ({file_path.name}): {e}")

    def process_and_rename(self, file_path: Path):
        # 1. ファイルの内容やメタデータの読み込み・解析を行います
        content_summary = self.extract_content(file_path)
        
        # 2. AI等を用いて新しいファイル名を決定します
        new_name = self.generate_new_filename(file_path, content_summary)
        
        if not new_name:
            print("有効な新しいファイル名が生成されませんでした。")
            return

        # 3. リネーム処理の実行（ファイルが存在していた元のサブディレクトリ内に保存します）
        parent_dir = file_path.parent
        new_path = parent_dir / f"{new_name}{file_path.suffix}"
        
        # 同名ファイルがすでに存在する場合、連番を付与して重複を回避します
        counter = 1
        while new_path.exists() and new_path != file_path:
            new_path = parent_dir / f"{new_name}_{counter}{file_path.suffix}"
            counter += 1

        # すでに同じ名前である場合はリネームをスキップします
        if new_path == file_path:
            return

        shutil.move(str(file_path), str(new_path))
        print(f"リネーム完了: {file_path} -> {new_path}")

    def extract_content(self, file_path: Path) -> str:
        # テキストファイル等から冒頭の文字列を抽出します（必要に応じて拡張子別のパーサーに拡張可能）
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(1000)
        except Exception:
            return "Binary or unreadable file content"

    def generate_new_filename(self, file_path: Path, content: str) -> str:
        # LLM（Ollama等）に問い合わせてファイル名を決定する処理のプレースホルダーです
        # ※必要に応じてクレンジング処理（clean_response）をここに組み込みます
        clean_name = "analyzed_document"
        return clean_name

def main():
    # 監視対象ディレクトリが存在しない場合は自動的に作成します
    if not WATCH_DIR.exists():
        WATCH_DIR.mkdir(parents=True, exist_ok=True)
        
    event_handler = FileRenameHandler()
    observer = Observer()
    
    # recursive=True を指定することで、target_folder 配下のすべてのサブディレクトリを再帰的に監視します
    observer.schedule(event_handler, path=str(WATCH_DIR), recursive=True)
    
    print(f"フォルダの再帰的監視を開始します: {WATCH_DIR.resolve()}")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        
    observer.join()

if __name__ == "__main__":
    main()