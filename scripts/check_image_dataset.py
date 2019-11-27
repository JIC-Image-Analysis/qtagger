import click
import dtoolcore


def check_dataset(ds):

    for idn in ds.identifiers:
        print(ds.item_properties(idn)['relpath'])


@click.command()
@click.argument('dataset_uri')
def main(dataset_uri):
    ds = dtoolcore.DataSet.from_uri(dataset_uri)

    check_dataset(ds)
    

if __name__ == "__main__":
    main()
