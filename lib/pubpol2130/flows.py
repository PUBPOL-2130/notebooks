"""Utilities for interacting with FlowmapBlue."""

import pandas as pd
import gspread_pandas

from tqdm import tqdm


def google_sheets_credentials():
    try: 
        from google.colab import auth
        from google.auth import default
    except ImportError:
        try:
            return gspread_pandas.conf.get_creds()
        except OSError as ex:
            print("Not running in Google Colab, and no local Google API credentials are available. :(")
            print("You'll need to generate API credentials for Google Sheets.")
            print(
                "See https://medium.com/@a.marenkov/how-to-get-credentials-for-google-sheets-456b7e88c430 "
                "for instructions."
            )
            raise ex

    auth.authenticate_user()
    creds, _ = default()
    return creds


def generate_flow_sheet(
    sheet_creds,
    locations_df,
    sheet_title: str,
    flows: dict[str, pd.DataFrame],
    flow_title: str = "",
    description: str = "",
    created_by_name: str = "",
    created_by_email: str = "",
    incoming_tooltip: str = "",
    outgoing_tooltip: str = "",
    flow_tooltip: str = "",
    total_unit: str = "units",
    data_source_name: str = "",
    data_source_url: str = "",
    color_scheme: str = "SunsetDark",
):
    # Anonymous read-only permissions required for FlowmapBlue.
    permissions = ["anyone"]
    if created_by_email:
        permissions.append(f"{created_by_email}||writer")
    
    props_df = pd.DataFrame(
        [
            {"property": "title", "value": flow_title},
            {"property": "description", "value": description},
            {"property": "source.name", "value": data_source_name},
            {"property": "source.url", "value": data_source_url},
            {"property": "createdBy.name", "value": created_by_name},
            {"property": "createdBy.email", "value": created_by_email},
            {"property": "colors.scheme", "value": color_scheme},
            {"property": "colors.darkMode", "value": "no"},
            {"property": "animate.flows", "value": "no"},
            {"property": "clustering", "value": "yes"},
            {
                "property": "flows.sheets",
                "value": ",".join(flows),
            },  # TODO: force plaintext cell type
            {"property": "msg.locationTooltip.incoming", "value": incoming_tooltip},
            {"property": "msg.locationTooltip.outgoing", "value": outgoing_tooltip},
            {"property": "msg.flowTooltip.numOfTrips", "value": flow_tooltip},
            {"property": "msg.totalCount.allTrips", "value": "{0} " + total_unit},
            {
                "property": "msg.totalCount.countOfTrips",
                "value": "{0} of {1} " + total_unit,
            },
        ]
    )
    props_spread = gspread_pandas.Spread(
        sheet_title,
        "properties",
        creds=sheet_creds,
        create_spread=True,
        create_sheet=True,
        permissions=permissions,
    )
    props_spread.clear_sheet()
    props_spread.df_to_sheet(
        props_df,
        index=False,
        headers=True,
        start="A1",
    )

    locations_spread = gspread_pandas.Spread(
        sheet_title,
        "locations",
        creds=sheet_creds,
        create_sheet=True,
    )
    locations_spread.clear_sheet()
    locations_spread.df_to_sheet(
        locations_df,
        index=False,
        headers=True,
        start="A1",
    )

    for key, df in tqdm(flows.items()):
        flow_spread = gspread_pandas.Spread(
            sheet_title,
            key,
            creds=sheet_creds,
            create_sheet=True,
        )
        flow_spread.clear_sheet()
        flow_spread.df_to_sheet(
            df,
            index=False,
            headers=True,
            start="A1",
        )
            
    return props_spread