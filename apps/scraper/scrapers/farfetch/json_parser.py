from typing import List

from apps.scraper.scraper_core.logger import get_logger
from apps.scraper.scraper_core.models import BaseImage, BaseOffer
from apps.scraper.scraper_core.utils import clean_text, validate_price

from .domain import FarfetchProduct, ProductVariant

logger = get_logger(__name__)


class FarfetchJSONParser:
    """Парсер JSON-LD данных для Farfetch."""

    def parse_product(self, json_data: dict, url: str, additional_info: dict) -> FarfetchProduct:
        """Парсинг товара из JSON-LD данных."""
        if not self._has_valid_json_data(json_data):
            logger.warning("JSON-LD данные недоступны, используем HTML селекторы")
            return self._create_product_from_html(additional_info, url)
        return self._create_product_from_json(json_data, additional_info, url)

    def _has_valid_json_data(self, json_data: dict) -> bool:
        """Проверка валидности JSON-LD данных."""
        return json_data and json_data.get("@type") == "ProductGroup"

    def _create_product_from_json(
        self, json_data: dict, additional_info: dict, url: str
    ) -> FarfetchProduct:
        """Создание продукта из JSON-LD данных."""
        product_data = self._extract_product_data(json_data, additional_info)
        filtered_additional_info = self._filter_additional_info(additional_info)
        return FarfetchProduct(
            name=product_data["name"],
            brand=product_data["brand"],
            color=product_data["color"],
            description=product_data["description"],
            product_group_id=product_data["product_group_id"],
            images=self._parse_product_images(json_data, additional_info),
            variants=self._parse_product_variants(json_data, additional_info),
            url=json_data.get("url", url),
            **filtered_additional_info,
        )

    def _extract_product_data(self, json_data: dict, additional_info: dict) -> dict:
        """Извлечение основных данных продукта."""
        return {
            "name": clean_text(json_data.get("name", "")) or additional_info.get("title", ""),
            "brand": json_data.get("brand", {}).get("name", "") or additional_info.get("brand", ""),
            "description": clean_text(json_data.get("description", ""))
            or additional_info.get("description", ""),
            "color": json_data.get("color", ""),
            "product_group_id": json_data.get("productGroupID", ""),
        }

    def _filter_additional_info(self, additional_info: dict) -> dict:
        """Фильтрация дополнительной информации."""
        excluded_fields = [
            "name",
            "brand",
            "description",
            "url",
            "images",
            "sizes",
            "price",
            "title",
        ]
        return {k: v for k, v in additional_info.items() if k not in excluded_fields}

    def _parse_product_variants(
        self, json_data: dict, additional_info: dict = None
    ) -> List[ProductVariant]:
        """Парсинг вариантов товара."""
        variants = []

        for variant_data in json_data.get("hasVariant", []):
            try:
                price_spec = variant_data.get("offers", {}).get("priceSpecification", [])
                if not price_spec or not validate_price(price_spec[0].get("price", 0)):
                    continue

                offer = BaseOffer(
                    url=variant_data.get("offers", {}).get("url", ""),
                    availability=variant_data.get("offers", {}).get("availability", "InStock"),
                    price_specification=price_spec,
                )

                variant = ProductVariant(
                    sku=variant_data.get("sku", ""),
                    name=clean_text(variant_data.get("name", "")),
                    size=variant_data.get("size", ""),
                    image=variant_data.get("image", ""),
                    offers=offer,
                )

                variants.append(variant)

            except Exception as e:
                logger.warning(f"Ошибка при парсинге варианта: {e}")
                continue

        logger.debug(f"Извлечено вариантов: {len(variants)}")
        return variants

    def _parse_product_images(
        self, json_data: dict, additional_info: dict = None
    ) -> List[BaseImage]:
        """Парсинг изображений товара."""
        images = []

        for image_data in json_data.get("image", []):
            try:
                image = BaseImage(
                    content_url=image_data.get("contentUrl", ""),
                    description=clean_text(image_data.get("description", "")),
                )
                images.append(image)

            except Exception as e:
                logger.warning(f"Ошибка при парсинге изображения: {e}")
                continue

        logger.debug(f"Извлечено изображений: {len(images)}")
        return images

    def _create_product_from_html(self, additional_info: dict, url: str) -> FarfetchProduct:
        """Создание продукта из HTML данных."""
        logger.info("Создаем продукт из HTML селекторов")
        html_images = additional_info.get("images", [])
        images = []
        for img_url in html_images:
            images.append(BaseImage(content_url=img_url, description=""))
        sizes = additional_info.get("sizes", [])
        variants = []
        for size in sizes:
            variant = ProductVariant(
                sku=f"html-{size}",
                name=f"{additional_info.get('title', '')} | {size}",
                size=size,
                image=html_images[0] if html_images else "",
                offers=BaseOffer(
                    url=url, availability="InStock", price_specification=[{"price": 0}]
                ),
            )
            variants.append(variant)
        if not variants:
            variants.append(
                ProductVariant(
                    sku="html-default",
                    name=additional_info.get("title", ""),
                    size="",
                    image=html_images[0] if html_images else "",
                    offers=BaseOffer(
                        url=url, availability="InStock", price_specification=[{"price": 0}]
                    ),
                )
            )
        return FarfetchProduct(
            name=additional_info.get("title", ""),
            brand=additional_info.get("brand", ""),
            color="",
            description=additional_info.get("description", ""),
            product_group_id="",
            images=images,
            variants=variants,
            url=url,
        )
