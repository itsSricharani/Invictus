from pipeline.data_repository import load_unified_data


def test_repository():

    df = load_unified_data()

    print("\nUnified Dataset:\n")

    print(df.tail())

    print("\nTotal Records:", len(df))

    print("\nAvailable Dates:")

    print(
        sorted(
            df["date"].unique()
        )
    )


if __name__ == "__main__":
    test_repository()