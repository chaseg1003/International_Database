drop database if exists census_data;
create database census_data;
use census_data;

create table country_stats (
	geo_id varchar(20) not null,
	year int not null,
	life_expectancy float,
	infant_mortality float,
	population_density float,
	sex_ratio float,
	dependency_ratio float,
	fertility_rate float,
	primary key (geo_id, year)
);

create table fertility_rates(
    geo_id varchar(20) not null,
    year int not null,
    age_group varchar(10),
    fertility_rate float,
    primary key (geo_id, year, age_group),
    foreign key (geo_id, year) references country_stats(geo_id, year)
);