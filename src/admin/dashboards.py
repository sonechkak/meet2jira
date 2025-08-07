from typing import Any

from fastadmin import (DashboardWidgetAdmin, DashboardWidgetType, WidgetType,
                       register_widget)
from pydantic import fields
from pydantic.v1.main import Model


class DashboardUser(Model):
    username = fields.CharField(max_length=255, unique=True)
    hash_password = fields.CharField(max_length=255)
    is_superuser = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=False)

    def __str__(self):
        return self.username


@register_widget
class UsersDashboardWidgetAdmin(DashboardWidgetAdmin):
    title = "Users"
    dashboard_widget_type = DashboardWidgetType.ChartLine

    x_field = "date"
    x_field_filter_widget_type = WidgetType.DatePicker
    x_field_filter_widget_props: dict[str, str] = {"picker": "month"}  # noqa: RUF012
    x_field_periods = ["day", "week", "month", "year"]  # noqa: RUF012

    y_field = "count"


class DashboardWidgetAdmin:
    title: str
    dashboard_widget_type: DashboardWidgetType
    x_field: str
    y_field: str | None = None
    series_field: str | None = None
    x_field_filter_widget_type: WidgetType | None = None
    x_field_filter_widget_props: dict[str, Any] | None = None
    x_field_periods: list[str] | None = None

    async def get_data(
        self,
        min_x_field: str | None = None,
        max_x_field: str | None = None,
        period_x_field: str | None = None,
    ) -> dict[str, Any]:
        """This method is used to get data for dashboard widget."""
        raise NotImplementedError
