# Fungi Orthology Data Pipeline

This project automates the retrieval and processing of fungal genome metadata from the [JGI MycoCosm](https://mycocosm.jgi.doe.gov/fungi/fungi.info.html) portal. It downloads the genome table, fetches file metadata for published organisms, and exports the results to CSV.

## Directory Structure

```
fungi_orthology/
│
├── config.py
├── credentials.py
├── src/
│   ├── mycocosm-datadump.py
│   └── utils/
│       ├── webutils.py
│       └── wrangleutils.py
│
└── local_data/
    └── mycocosm_data/
        ├── mycocosm_fungi_data.csv
        ├── mycocosm_fungi_files_metadata.csv
        └── json_files/
```

## Setup

1. **Clone the repository** and navigate to the project folder.
2. **Install dependencies** (recommended: use a virtual environment):

    ```
    pip install -r requirements.txt
    ```

    Required packages include: `requests`, `beautifulsoup4`, `pandas`.

3. **Configure credentials**  
   Edit `credentials.py` and set your JGI API token:

    ```python
    JGI_API_TOKEN = "your_token_here"
    ```

4. **Adjust configuration**  
   Edit `config.py` if you need to change data paths or API settings.

## Usage

Run the main data pipeline from the project root:

```
python src/mycocosm-datadump.py
```

This will:
- Download the MycoCosm fungi genome table.
- Filter for published organisms.
- Fetch file metadata for each organism (using the JGI API).
- Save results to CSV files in `local_data/mycocosm_data/`.

## Output Files

- `mycocosm_fungi_data.csv`: Table of all fungi genomes from MycoCosm.
- `mycocosm_fungi_files_metadata.csv`: Metadata for files associated with published organisms.
- `json_files/`: Raw JSON responses from the JGI API.

## Customization

- **Change the number of parallel API requests**: Edit `max_workers` in `webutils.py`.
- **Change request delay**: Adjust `REQUEST_DELAY` in `config.py`.

## Troubleshooting

- Ensure your API token is valid.
- If you encounter import errors, run scripts from the project root.
- For large downloads, ensure a stable internet connection.

## License

This project is for research and educational use.  
**Do not share your API token or upload modified credentials.py.**

---

**Contact:**  
For questions or issues, open an issue or contact the