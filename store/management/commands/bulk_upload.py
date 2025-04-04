import csv
from django.core.management.base import BaseCommand, CommandError
from store.models import Category, Unit, Product, Variant, CountryOfOrigin


class Command(BaseCommand):
    help = 'Bulk upload products and variants from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str,
                            help='The CSV file to import data from')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                products_cache = {}

                for row in reader:
                    # Get or create Category
                    category, _ = Category.objects.get_or_create(
                        name=row['category'])

                    # Get or create Unit
                    unit, _ = Unit.objects.get_or_create(name=row['unit'])

                    # Get or create CountryOfOrigin
                    country_of_origin, _ = CountryOfOrigin.objects.get_or_create(
                        name=row['country_of_origin'])

                    # Check if the product already exists in cache or in the database
                    product_key = (row['product_name'],
                                   row['brand_name'], row['category'])
                    if product_key not in products_cache:
                        product, _ = Product.objects.get_or_create(
                            category=category,
                            name=row['product_name'],
                            defaults={
                                'brand_name': row.get('brand_name', ''),
                                'type': row.get('type', 'OTC'),
                                'sub_description': row.get('sub_description', ''),
                                'how_to_use': row.get('how_to_use', ''),
                                'side_effects': row.get('side_effects', ''),
                                'drug_interactions': row.get('drug_interactions', ''),
                                'precautions': row.get('precautions', ''),
                                'featured': row.get('featured', 'False').lower() == 'true',
                                'sale': row.get('sale', 'False').lower() == 'true',
                                'top_selling': row.get('top_selling', 'False').lower() == 'true',
                            }
                        )
                        products_cache[product_key] = product
                    else:
                        product = products_cache[product_key]

                    # Create Variant based on potency and number of tablets
                    variant_key = (
                        product.id, row['potency'], row['number_of_tablets'])
                    variant, created = Variant.objects.get_or_create(
                        product=product,
                        unit=unit,
                        potency=row['potency'],
                        number_of_tablets=row['number_of_tablets'],
                        country_of_origin=country_of_origin,
                        defaults={
                            'price_inr': row['price_inr'],
                            'price_usd': row['price_usd'],
                            'original_price_usd': row.get('original_price_usd', None),
                            'manufacturer': row['manufacturer'],
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f"Created variant for product: {product.name}, Potency: {row['potency']}mg, Tablets: {row['number_of_tablets']}"))
                    else:
                        self.stdout.write(self.style.SUCCESS(
                            f"Updated variant for product: {product.name}, Potency: {row['potency']}mg, Tablets: {row['number_of_tablets']}"))

        except FileNotFoundError:
            raise CommandError('CSV file does not exist')
        except Exception as e:
            raise CommandError(f"Error: {e}")

        self.stdout.write(self.style.SUCCESS('Data upload complete'))
