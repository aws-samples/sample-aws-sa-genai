SELECT COALESCE("d"."accountid", "g"."account_id") "accountid",
	COALESCE("g"."user", "d"."user_name") "user_name",
	COALESCE("g"."user_arn", "d"."user_arn") "user_arn",
	"d"."awsregion",
	replace("d"."dashboard_name", '"', '') "dashboard_name",
	"d"."dashboardid",
	"d"."event_time",
	"dv1"."last_view_dashboard_time",
	"ev1"."last_event_time",
	"ev1"."first_event_time",
	"g"."namespace",
	"g"."group",
	"g"."email",
	"g"."role",
	COALESCE("g"."identity_type", 'QUICKSIGHT') "identity_type",
	"do1"."principal_name" "owner_viewer",
	"do1"."ownership" "ownership"
FROM (
		(
			(
				SELECT "useridentity"."accountid",
					"useridentity"."type",
					"split_part"(
						"useridentity"."sessioncontext"."sessionissuer"."arn",
						'/',
						2
					) "assumed_role",
					"useridentity"."arn" "user_arn",
					COALESCE(
						"useridentity"."username",
						"concat"(
							"split_part"("useridentity"."arn", '/', 2),
							'/',
							"split_part"("useridentity"."arn", '/', 3)
						)
					) "user_name",
					"awsregion",
					"split_part"(
						"split_part"("serviceeventdetails", 'dashboardName":', 2),
						',',
						1
					) "dashboard_name",
					"split_part"(
						"split_part"(
							"split_part"(
								"split_part"("serviceeventdetails", 'dashboardId":', 2),
								',',
								1
							),
							'dashboard/',
							2
						),
						'"}',
						1
					) "dashboardId",
					"date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ') "event_time"
				FROM "admin-console-2025"."cloudtrail_logs_pp"
				WHERE "eventsource" = 'quicksight.amazonaws.com'
					AND "eventname" = 'GetDashboard'
					AND (
						"date_trunc"('day', "date_parse"("timestamp", '%Y/%m/%d')) > CAST((current_date - INTERVAL '99' DAY) AS date)
					)
				GROUP BY 1,
					2,
					3,
					4,
					5,
					6,
					7,
					8,
					9
			) d
			left join (
				SELECT "useridentity"."arn" "user_arn",
					max("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) "last_view_dashboard_time"
				FROM "admin-console-2025"."cloudtrail_logs_pp"
				WHERE "eventsource" = 'quicksight.amazonaws.com'
					AND "eventname" = 'GetDashboard'
					AND (
						"date_trunc"('day', "date_parse"("timestamp", '%Y/%m/%d')) > CAST((current_date - INTERVAL '99' DAY) AS date)
					)
				GROUP BY 1
			) dv1 ON "d"."user_arn" = "dv1"."user_arn"
			left join (
				SELECT "useridentity"."arn" "user_arn",
				min("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) "first_event_time",
					max("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) "last_event_time"
				FROM "admin-console-2025"."cloudtrail_logs_pp"
				WHERE "eventsource" = 'quicksight.amazonaws.com'
					AND (
						"date_trunc"('day', "date_parse"("timestamp", '%Y/%m/%d')) > CAST((current_date - INTERVAL '99' DAY) AS date)
					)
				GROUP BY 1
			) ev1 on "d"."user_arn" = "ev1"."user_arn"
			FULL JOIN "admin-console-2025".group_membership g ON "d"."user_arn" = "g"."user_arn"
			OR (
				("d"."accountid" = "g"."account_id")
				AND ("d"."user_name" = "g"."user")
			)
		)
		LEFT JOIN (
			SELECT "account_id",
				"aws_region",
				"object_id",
				"object_name",
				"principal_type",
				"principal_name",
				"arn",
				"namespace",
				(
					CASE
						WHEN ("strpos"("permissions", 'Delete') <> 0) THEN 'Owner' ELSE 'Viewer'
					END
				) "Ownership"
			FROM "admin-console-2025".object_access
			WHERE ("object_type" = 'dashboard')
				AND ("principal_type" in ('group', 'user'))
			GROUP BY 1,
				2,
				3,
				4,
				5,
				6,
				7,
				8,
				9
		) do1 ON "d"."dashboardid" = "do1"."object_id"
		AND "do1"."arn" = "d"."user_arn"
		OR (
			(
				(
					(
						("d"."accountid" = "do1"."account_id")
						AND ("d"."awsregion" = "do1"."aws_region")
					)
					AND ("d"."dashboardid" = "do1"."object_id")
				)
				AND (
					"do1"."principal_name" = "g"."group"
					OR "do1"."principal_name" = "d"."user_name"
				)
			)
			AND "do1"."namespace" = "g"."namespace"
		)
	)
GROUP BY 1,
	2,
	3,
	4,
	5,
	6,
	7,
	8,
	9,
	10,
	11,
	12,
	13,
	14,
	15,
	16,
	17